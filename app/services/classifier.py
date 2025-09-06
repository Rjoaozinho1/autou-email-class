import json
import re
from ..core.logging import logger
from ..core.settings import CLASSIFICATION_TEMPERATURE
from .groq_client import groq_chat


def classify_email(text: str) -> tuple[str, str]:
    """
    Usa Groq com um prompt de classificação. Pede resposta estrita JSON para robustez.
    """

    email_excerpt = text
    system = """
    Você é um classificador rigoroso de emails corporativos em pt-BR para uma empresa do setor financeiro. Sua missão é, para CADA email recebido, (1) classificar como "Produtivo" ou "Improdutivo"; (2) sugerir uma resposta automática sucinta em pt-BR de acordo com a classificacao; (3) retornar TUDO em JSON válido, sem qualquer texto extra.

    # Informacoes
    Esses emails podem ser mensagens solicitando um status atual sobre uma requisição em andamento, compartilhando algum arquivo ou até mesmo mensagens improdutivas, como desejo de feliz natal ou perguntas não relevantes. 

    # Classificacao
        - Produtivo: requer ação/resposta específica do time (ex.: solicitação de suporte, pedido de status/atualização de caso, dúvida técnica, envio/solicitação de documentos relevantes, alinhamento operacional, ajuste de acesso/credencial, incidentes, cobrança contestada, compliance/KYC), classifique como Produtivo.

        - Improdutivo: não requer ação imediata (ex.: felicitações/agradecimentos, mensagens genéricas, “FYI” sem pedido, ausência, ooo/marketing não solicitado, spam). Se o conteúdo pede ação mas já foi resolvido no próprio email (sem pendência) e não solicita confirmação, classifique como Improdutivo.

    # Regras de decisão
    1) **Phishing/Spam suspeito?** Se forte indício (links estranhos, anexos executáveis, pedido de credenciais): label=Improdutivo.
    2) **OOO/ausência automática?** (palavras como \"fora do escritório\", \"volto em\", “automatic reply”): label=Improdutivo.
    3) **Existe pedido claro, prazo, pergunta objetiva ou referência a ticket/caso?**: label=Produtivo.
    4) **Apenas cortesia/agradecimento/felicitação sem pedido?**: label=Improdutivo.
    5) **Compartilha documentos relevantes a um processo em andamento?**: label=Produtivo
    6) **Conteúdo ambíguo:** Se há chance razoável de que o time precise agir (ex.: “segue em anexo o relatório deste mês”): label=Produtivo.

    # Sugestão de resposta automática (pt-BR, tom profissional, 80-180 palavras)
    - Para Produtivo: reconheça o pedido, cite o ID/caso se houver, diga próximo passo e prazo padrão (ou o prazo detectado), peça o que faltar (documento, print, número do caso). Evite promessas fortes; prefira \"estamos analisando\".
    - Para Improdutivo:
    • greeting/thank_you: resposta curta e cordial (≤40 palavras).
    • ooo/spam_phishing/newsletter_marketing: sugerir_reply vazio.
    - Nunca inclua links suspeitos. Não peça dados sensíveis desnecessários.

    # Formato de saída (obrigatório, JSON estrito)
    Retorne **apenas** um objeto JSON com as chaves:
    {
        \"label\": \"Produtivo\" | \"Improdutivo\",
        \"suggested_reply\": \"Resposta sobre o email em pt-BR\"
    }

    # Observâncias
    - Respeite LGPD: não exponha dados sensíveis além do mínimo necessário.
    - Nunca faça suposições inventadas; se não há dado, deixe o campo vazio/omitido conforme o esquema.
    - Nunca imprima texto fora do JSON. **Sem** markdown, sem comentários.

    # Exemplos (few-shot)

    [Exemplo 1 — Produtivo/status_update]
    Email:
    \"Bom dia, poderiam informar o status do chamado CASE#54821 sobre a integração com o ERP Y? Precisamos de um posicionamento até 06/09.\"
    Saída esperada:
    {
        \"label\":\"Produtivo\",
        \"suggested_reply\":\"Olá! Identificamos o chamado CASE#54821 e estamos analisando a integração com o ERP Y. Retornaremos com atualização até 06/09. Se possível, envie prints de erro ou logs recentes para acelerarmos. Permanecemos à disposição.\"
    }

    [Exemplo 2 — Produtivo/document_share]
    Email:
    \"Segue em anexo o relatório de conformidade solicitado para o dossiê do cliente 123. Precisando de algo mais, avisem.\"
    Saída esperada:
    {
        \"label\":\"Produtivo\",
        \"suggested_reply\":\"Obrigado pelo envio do relatório de conformidade do cliente 123. Vamos validar o documento e retornamos caso falte alguma peça. Se houver versão atualizada ou comprovantes adicionais, pode nos encaminhar.\"
    }

    [Exemplo 3 — Improdutivo/greeting]
    Email:
    \"Feliz Natal a toda a equipe! Muito sucesso!\"
    Saída esperada:
    {
        \"label\":\"Improdutivo\",
        \"suggested_reply\":\"Agradecemos a mensagem e desejamos ótimas festas!\"
    }

    [Exemplo 5 — Improdutivo/spam_phishing]
    Email:
    \"Atualize sua senha do banco aqui: http://banco-seguro-login.xyz anexamos arquivo .exe para facilitar.\"
    Saída esperada:
    {
        \"label\":\"Improdutivo\",
        \"suggested_reply\":\"\"
    }

    [Fim dos exemplos]

    Lembrete final: sua resposta deve ser APENAS o JSON, válido e bem formatado, conforme o esquema acima.
    """

    user = f"EMAIL:\n\"\"\"\n{email_excerpt}\n\"\"\""

    out = groq_chat(
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=CLASSIFICATION_TEMPERATURE,
        max_tokens=128,
    )

    label = None
    reply = None

    try:
        logger.info(f"Raw Groq output: {out}")
        data = json.loads(out)
        label = str(data.get("label", "")).strip()
        reply = str(data.get("suggested_reply", "")).strip()
    except Exception:
        m = re.search(r'"label"\s*:\s*"(?P<label>[^"]+)"', out, re.IGNORECASE)
        r = re.search(r'"suggested_reply"\s*:\s*"(?P<reply>[^"]+)"', out, re.IGNORECASE)

        if m and r:
            label = m.group("label").strip()
            reply = r.group("suggested_reply").strip() if r else ""
        elif m:
            label = m.group("label").strip()
        elif r:
            reply = r.group("suggested_reply").strip()
        else:
            label = (out or "").strip()
            reply = (out or "").strip()

    final = None
    label_norm = (label or "").lower()
    if "produtivo" in label_norm or "Produtivo" in (label or ""):
        final = "Produtivo"
    elif "improdutivo" in label_norm or "Improdutivo" in (label or ""):
        final = "Improdutivo"
    else:
        final = label or "Improdutivo"

    logger.info(f"classification -> raw='{out}' | label='{final}'")

    return final, (reply or "")

