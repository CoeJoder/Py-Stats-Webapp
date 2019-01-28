import io
import os
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import fileupload


def show_import_button():

    _upload_widget = fileupload.FileUploadWidget(label="Import Spreadsheet")

    def _cb(change):
        #decoded = io.StringIO(change['owner'].data.decode('utf-8'))
        filename = change['owner'].filename
        #print('Uploaded `{}` ({:.2f} kB)'.format(filename, len(decoded.read()) / 2 **10))
        clear_output(wait=True)
        display(HTML("<h1>File uploaded: {}</h1>".format(filename)))

    _upload_widget.observe(_cb, names='data')
    display(_upload_widget)

