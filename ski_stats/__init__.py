from flask import Flask
import pkgutil
import ski_stats.scripts

app = Flask(__name__)
app.config["WTF_CSRF_ENABLED"] = False

# load the analysis modules
analyses = []
for index, (importer, modname, ispkg) in enumerate(pkgutil.walk_packages(path=ski_stats.scripts.__path__, onerror=lambda x: None)):
    if not ispkg:
        print "[{0}] Found analysis module \"{1}\"".format(index, modname)
        module = importer.find_module(modname).load_module(modname)

        # load script if defines these two functions
        if hasattr(module, "get_html_form") and hasattr(module.get_html_form, "__call__") \
                and hasattr(module, "html_form_submitted") and hasattr(module.html_form_submitted, "__call__"):
            analyses.append({"id": index, "name": modname, "module": module})

# load the HTTP routes
import ski_stats.views

