import azure.functions as func

app = func.FunctionApp()

from triggers.carga_itsm import app as carga_itsm

app.register_functions(carga_itsm)
