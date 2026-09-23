import azure.functions as func

from etl.catalogo import AGENDADOR

app = func.Blueprint()


@app.timer_trigger(schedule="0 */3 * * * *", arg_name="myTimer",
                   run_on_startup=False, use_monitor=False)
def carga_itsm(myTimer: func.TimerRequest) -> None:
    AGENDADOR.disparar("carga_itsm")
