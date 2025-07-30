from flask import current_app, abort

@app.route("/executar-creditos/<token>")
def executar_creditos(token):
    # Token de segurança
    TOKEN_ESPERADO = "S3guroToken@2025"

    if token != TOKEN_ESPERADO:
        abort(403)

    from cashflex_app.jobs import distribuir_rendimentos
    distribuir_rendimentos()
    return "Rendimentos distribuídos com sucesso."


