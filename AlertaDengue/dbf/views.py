from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import File
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView

from dbf.models import DBF, DBFChunkedUpload
from dbf.forms import DBFForm

class UploadSuccessful(LoginRequiredMixin, TemplateView):
    template_name = "upload_successful.html"


class Upload(LoginRequiredMixin, FormView):
    form_class = DBFForm
    template_name = "dbf_upload.html"
    success_url = reverse_lazy("dbf:upload_successful")

    def post(self, request, *args, **kwargs):
        self.request.POST['uploaded_by'] = request.user.id
        return super(Upload, self).post(self.request, *args, **kwargs)

    def form_valid(self, form):
        chunked_upload = DBFChunkedUpload.objects.get(
            id=form.cleaned_data['chunked_upload_id'],
            user=self.request.user
        )
        uploaded_file = File(chunked_upload.file, form.cleaned_data['filename'])
        dbf = DBF.objects.create(
            uploaded_by=self.request.user,
            file=uploaded_file,
            export_date=form.cleaned_data['export_date'],
            notification_year=form.cleaned_data['notification_year']
        )
        return super(Upload, self).form_valid(form)


    def get_context_data(self, **kwargs):
        kwargs['last_uploaded'] = DBF.objects.filter(uploaded_by=self.request.user)[:5]
        return super(Upload, self).get_context_data(**kwargs)


class DBFChunkedUploadView(ChunkedUploadView):

    model = DBFChunkedUpload
    field_name = 'the_file'


class DBFChunkedUploadCompleteView(ChunkedUploadCompleteView):

    model = DBFChunkedUpload

    def on_completion(self, uploaded_file, request):
        # Do something with the uploaded file. E.g.:
        # * Store the uploaded file on another model:
        # SomeModel.objects.create(user=request.user, file=uploaded_file)
        # * Pass it as an argument to a function:
        # function_that_process_file(uploaded_file)
        pass

    def get_response_data(self, chunked_upload, request):
        #return {'message': ("You successfully uploaded '%s' (%s bytes)!" %
        #                    (chunked_upload.filename, chunked_upload.offset))}
        return {'filename': chunked_upload.filename, 'chunked_upload_id': chunked_upload.id}
