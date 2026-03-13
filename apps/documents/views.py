from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from apps.accounts.models import UserRole
from apps.core.activity import log_activity
from apps.core.models import ActivitySubject

from .forms import CompanyDocumentForm
from .models import CompanyDocument, DocumentCategory


class DocumentAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = (UserRole.ADMIN, UserRole.CHEF)

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in self.allowed_roles


class DocumentListView(DocumentAccessMixin, ListView):
    model = CompanyDocument
    template_name = "documents/document_list.html"
    context_object_name = "documents"

    def get_queryset(self):
        queryset = CompanyDocument.objects.select_related("uploaded_by")
        query = self.request.GET.get("q", "").strip()
        category = self.request.GET.get("category", "").strip()
        if query:
            queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(file__icontains=query))
        if category and category in dict(DocumentCategory.choices):
            queryset = queryset.filter(category=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        context["active_category"] = self.request.GET.get("category", "").strip()
        context["category_choices"] = DocumentCategory.choices
        return context


class DocumentCreateView(DocumentAccessMixin, CreateView):
    model = CompanyDocument
    template_name = "documents/document_form.html"
    form_class = CompanyDocumentForm
    success_url = reverse_lazy("documents:document_list")

    def form_valid(self, form):
        form.instance.uploaded_by = self.request.user
        response = super().form_valid(form)
        log_activity(
            actor=self.request.user,
            subject_type=ActivitySubject.DOKUMENT,
            subject_label=self.object.title,
            action="Dokument hochgeladen",
            details=f"Datei: {self.object.file.name.split('/')[-1]}",
            icon="📄",
        )
        messages.success(self.request, "Dokument wurde hochgeladen.")
        return response


class DocumentDetailView(DocumentAccessMixin, DetailView):
    model = CompanyDocument
    template_name = "documents/document_detail.html"
    context_object_name = "document"


class DocumentUpdateView(DocumentAccessMixin, UpdateView):
    model = CompanyDocument
    template_name = "documents/document_form.html"
    form_class = CompanyDocumentForm

    def get_success_url(self):
        return reverse_lazy("documents:document_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        old = self.get_object()
        old_category = old.get_category_display()
        response = super().form_valid(form)
        log_activity(
            actor=self.request.user,
            subject_type=ActivitySubject.DOKUMENT,
            subject_label=self.object.title,
            action="Dokument bearbeitet",
            details="Metadaten oder Datei wurden aktualisiert.",
            from_state=old_category,
            to_state=self.object.get_category_display(),
            icon="🗂️",
        )
        messages.success(self.request, "Dokument wurde aktualisiert.")
        return response


class DocumentDeleteView(DocumentAccessMixin, DeleteView):
    model = CompanyDocument
    template_name = "documents/document_confirm_delete.html"
    success_url = reverse_lazy("documents:document_list")

    def form_valid(self, form):
        document = self.get_object()
        log_activity(
            actor=self.request.user,
            subject_type=ActivitySubject.DOKUMENT,
            subject_label=document.title,
            action="Dokument gelöscht",
            details=f"Datei: {document.file.name.split('/')[-1]}",
            icon="🗑️",
        )
        messages.success(self.request, "Dokument wurde gelöscht.")
        return super().form_valid(form)


class DocumentDownloadView(DocumentAccessMixin, View):
    def get(self, request, pk):
        document = get_object_or_404(CompanyDocument, pk=pk)
        if not document.file:
            raise Http404("Datei nicht gefunden.")
        return FileResponse(document.file.open("rb"), as_attachment=True, filename=document.file.name.split("/")[-1])


class DocumentBulkZipDownloadView(DocumentAccessMixin, View):
    def post(self, request):
        ids = request.POST.getlist("document_ids")
        if not ids:
            messages.warning(request, "Bitte mindestens ein Dokument auswählen.")
            return redirect("documents:document_list")

        documents = CompanyDocument.objects.filter(id__in=ids)
        if not documents.exists():
            messages.error(request, "Keine gültigen Dokumente ausgewählt.")
            return redirect("documents:document_list")

        archive_stream = BytesIO()
        with ZipFile(archive_stream, "w", ZIP_DEFLATED) as zip_file:
            for document in documents:
                if not document.file:
                    continue
                with document.file.open("rb") as doc_file:
                    zip_file.writestr(document.file.name.split("/")[-1], doc_file.read())

        archive_stream.seek(0)
        response = HttpResponse(archive_stream.getvalue(), content_type="application/zip")
        response["Content-Disposition"] = 'attachment; filename="firmendokumente.zip"'
        return response
