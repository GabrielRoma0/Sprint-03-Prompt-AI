"""
Gera os PDFs sintéticos que compõem a base de conhecimento desta pasta.

IMPORTANTE — natureza dos documentos: são materiais **sintéticos**,
escritos pelo grupo para fins acadêmicos (FIAP, Sprint 04), com
especificações plausíveis para o domínio GoodWe/EV (consistentes com os
enums e faixas de validação já usados em
`src/schemas/consulta_recarga.py`). Não são manuais oficiais da GoodWe
Brasil nem reproduzem texto de nenhum documento real do fabricante — cada
PDF tem um aviso dessa natureza na primeira página. Usar dados sintéticos
verossímeis é a alternativa explicitamente aceita pelo enunciado quando o
grupo não tem acesso à documentação proprietária real (§5: "base
expandida... manuais de produto GoodWe... regimentos... FAQs... tabelas
tarifárias").

Rodar:
    python data/knowledge_base/_gerar_pdfs_sinteticos.py

Prefixo `_` no nome do arquivo: convenção deste projeto para "não é
conteúdo da base, é o script que gera o conteúdo" — `src/rag/loader.py`
só varre `*.pdf` neste diretório, então este `.py` nunca é indexado.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUTPUT_DIR = Path(__file__).parent

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TituloDoc", fontSize=16, leading=20, spaceAfter=10, textColor=colors.HexColor("#0a3d62")))
styles.add(ParagraphStyle(name="Aviso", fontSize=8.5, leading=11.5, spaceAfter=12, textColor=colors.HexColor("#8a5a00"), backColor=colors.HexColor("#fff6e0"), borderPadding=6))
styles.add(ParagraphStyle(name="H1Doc", fontSize=12.5, leading=16, spaceBefore=12, spaceAfter=6, textColor=colors.HexColor("#0a3d62")))
styles.add(ParagraphStyle(name="H2Doc", fontSize=11, leading=14, spaceBefore=8, spaceAfter=4, textColor=colors.HexColor("#1a1a1a")))
styles.add(ParagraphStyle(name="CorpoDoc", fontSize=10, leading=14, spaceAfter=6))
styles.add(ParagraphStyle(name="CelulaCab", fontSize=9, leading=11, textColor=colors.white, fontName="Helvetica-Bold"))
styles.add(ParagraphStyle(name="Celula", fontSize=9, leading=11.5))

AVISO_SINTETICO = (
    "<b>Aviso:</b> este é um documento SINTÉTICO, escrito para fins acadêmicos "
    "(FIAP — Prompt and Artificial Intelligence, EV Challenge GoodWe, Sprint 04). "
    "Não é material oficial da GoodWe Brasil e não reproduz texto de nenhum "
    "manual, regimento ou tabela real do fabricante — as especificações e "
    "regras abaixo foram elaboradas pelo grupo para alimentar o pipeline RAG "
    "do projeto, com valores plausíveis e consistentes com o domínio."
)


def _tabela(linhas: list[list[str]], largura_primeira_col: float = 5.5) -> Table:
    cabecalho, *corpo = linhas
    dados = [[Paragraph(c, styles["CelulaCab"]) for c in cabecalho]]
    for linha in corpo:
        dados.append([Paragraph(c, styles["Celula"]) for c in linha])
    n_cols = len(cabecalho)
    largura_resto = (17 - largura_primeira_col) / max(n_cols - 1, 1)
    col_widths = [largura_primeira_col * cm] + [largura_resto * cm] * (n_cols - 1)
    tabela = Table(dados, colWidths=col_widths, repeatRows=1)
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a3d62")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f6fa")]),
            ]
        )
    )
    return tabela


def _doc(nome_arquivo: str, titulo: str, elementos: list) -> None:
    path = OUTPUT_DIR / nome_arquivo
    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    corpo = [
        Paragraph(titulo, styles["TituloDoc"]),
        Paragraph(AVISO_SINTETICO, styles["Aviso"]),
        *elementos,
    ]
    doc.build(corpo)
    print(f"Gerado: {path}")


def gerar_manual_chargegrid() -> None:
    el = [
        Paragraph("1. Visão geral", styles["H1Doc"]),
        Paragraph(
            "O GoodWe ChargeGrid é um carregador de veículos elétricos (EVSE) para uso "
            "residencial e comercial de pequeno porte, integrado à plataforma de gestão "
            "EV ChargeOps para monitoramento remoto, faturamento de sessões e diagnóstico "
            "de falhas. A linha ChargeGrid HCA G2 é o modelo de referência deste manual.",
            styles["CorpoDoc"],
        ),
        Paragraph("2. Especificações técnicas", styles["H1Doc"]),
        _tabela(
            [
                ["Especificação", "Valor"],
                ["Potência máxima (trifásico)", "22 kW AC"],
                ["Potência máxima (monofásico)", "7,4 kW AC"],
                ["Conector", "Tipo 2 (IEC 62196-2)"],
                ["Grau de proteção", "IP54 (uso externo coberto ou interno)"],
                ["Faixa de temperatura de operação", "-25°C a 50°C"],
                ["Proteção diferencial", "RCD Tipo B integrado (6 mA DC sensitive)"],
                ["Protocolo de comunicação", "OCPP 1.6J, compatível com EV ChargeOps"],
                ["Conectividade", "Wi-Fi 2,4 GHz e Ethernet RJ45"],
            ]
        ),
        Spacer(1, 10),
        Paragraph("3. Estados operacionais", styles["H1Doc"]),
        Paragraph(
            "O carregador reporta um dos cinco estados a seguir à plataforma EV "
            "ChargeOps, atualizados em tempo real:",
            styles["CorpoDoc"],
        ),
        ListFlowable(
            [
                ListItem(Paragraph("<b>Disponível</b> — sem veículo conectado, pronto para iniciar uma sessão.", styles["CorpoDoc"])),
                ListItem(Paragraph("<b>Em carga</b> — sessão ativa, entregando potência ao veículo.", styles["CorpoDoc"])),
                ListItem(Paragraph("<b>Concluído</b> — sessão finalizada (veículo atingiu carga completa ou usuário encerrou manualmente).", styles["CorpoDoc"])),
                ListItem(Paragraph("<b>Em falha</b> — erro detectado (ex.: falha de isolamento, sobrecorrente, falha de comunicação com o veículo); a sessão é interrompida automaticamente por segurança.", styles["CorpoDoc"])),
                ListItem(Paragraph("<b>Offline</b> — carregador sem comunicação com a plataforma EV ChargeOps; o histórico da sessão em andamento é sincronizado assim que a conexão for restabelecida.", styles["CorpoDoc"])),
            ],
            bulletType="bullet",
        ),
        Spacer(1, 10),
        Paragraph("4. Segurança e instalação", styles["H1Doc"]),
        Paragraph(
            "A instalação do ChargeGrid HCA G2 deve ser realizada exclusivamente por "
            "eletricista certificado, seguindo a NBR 17019 (instalações elétricas de "
            "recarga de veículos elétricos). O usuário final não deve abrir o gabinete "
            "do equipamento, substituir o disjuntor associado ou realizar qualquer "
            "intervenção na instalação elétrica — essas operações exigem certificação "
            "profissional e, se realizadas incorretamente, anulam a garantia do "
            "equipamento.",
            styles["CorpoDoc"],
        ),
        Paragraph(
            "Em caso de estado 'Em falha' persistente, o procedimento recomendado é: "
            "(1) verificar pela plataforma EV ChargeOps o código de erro reportado; "
            "(2) desconectar o veículo; (3) aguardar 5 minutos e tentar reiniciar a "
            "sessão pelo aplicativo; (4) se a falha persistir, contatar a assistência "
            "técnica autorizada GoodWe — não tentar reparo próprio.",
            styles["CorpoDoc"],
        ),
        Paragraph("5. Faturamento de sessão", styles["H1Doc"]),
        Paragraph(
            "Cada sessão de carga gera um registro com energia entregue (kWh), potência "
            "média (kW) e valor faturado (BRL), calculado conforme a tarifa vigente "
            "cadastrada na plataforma (ver tabela tarifária). O valor faturado de uma "
            "sessão já concluída pode ser consultado a qualquer momento pelo aplicativo "
            "ou assistente virtual — essa consulta não constitui aconselhamento "
            "financeiro, é apenas a leitura de um dado já registrado da sessão.",
            styles["CorpoDoc"],
        ),
    ]
    _doc("manual_chargegrid_evchargeops.pdf", "Manual de Produto — GoodWe ChargeGrid HCA G2 / Plataforma EV ChargeOps", el)


def gerar_regimento_condominial() -> None:
    el = [
        Paragraph("1. Objetivo", styles["H1Doc"]),
        Paragraph(
            "Este regimento estabelece as regras de uso dos pontos de recarga de "
            "veículos elétricos instalados na garagem compartilhada do condomínio, "
            "aplicáveis a todos os condôminos com vaga cadastrada no sistema de "
            "carregamento.",
            styles["CorpoDoc"],
        ),
        Paragraph("2. Horário de uso", styles["H1Doc"]),
        Paragraph(
            "O carregamento é permitido das 6h às 23h em qualquer ponto de recarga "
            "disponível, sem necessidade de reserva prévia. Entre 23h e 6h "
            "(carregamento noturno), o uso é permitido apenas mediante reserva prévia "
            "pelo aplicativo do condomínio, com no máximo uma reserva noturna ativa por "
            "unidade a cada 7 dias, para garantir acesso rotativo entre os condôminos "
            "interessados.",
            styles["CorpoDoc"],
        ),
        Paragraph("3. Rateio de custos", styles["H1Doc"]),
        Paragraph(
            "O custo de energia de cada sessão é individualizado por medição própria de "
            "cada ponto de recarga e cobrado diretamente ao condômino responsável na "
            "fatura mensal do condomínio, conforme a tarifa vigente (ver tabela "
            "tarifária) — não é rateado entre todos os condôminos, apenas quem usa "
            "paga pela energia consumida. A manutenção preventiva dos equipamentos "
            "compartilhados é rateada entre todas as unidades com vaga cadastrada no "
            "sistema, proporcionalmente à fração ideal de cada unidade.",
            styles["CorpoDoc"],
        ),
        Paragraph("4. Uso e boas práticas", styles["H1Doc"]),
        ListFlowable(
            [
                ListItem(Paragraph("O veículo deve ser retirado do ponto de recarga em até 30 minutos após o fim da sessão (estado 'Concluído'), para liberar o ponto a outro condômino.", styles["CorpoDoc"])),
                ListItem(Paragraph("É proibido o uso de extensões, adaptadores não homologados ou qualquer equipamento externo conectado ao carregador.", styles["CorpoDoc"])),
                ListItem(Paragraph("Qualquer estado 'Em falha' persistente deve ser reportado à administração do condomínio, além do procedimento técnico do manual do fabricante.", styles["CorpoDoc"])),
            ],
            bulletType="bullet",
        ),
        Spacer(1, 8),
        Paragraph("5. Responsabilidade por danos", styles["H1Doc"]),
        Paragraph(
            "Danos ao equipamento comprovadamente causados por mau uso (ex.: uso de "
            "adaptador não homologado, tentativa de abertura do gabinete pelo próprio "
            "condômino) são de responsabilidade financeira da unidade responsável pela "
            "sessão no momento do dano, apurada pelos registros da plataforma EV "
            "ChargeOps. Casos que envolvam disputa sobre responsabilidade ou valores "
            "devem ser encaminhados à administração do condomínio — este assistente "
            "não decide sobre responsabilidade de dano nem orienta sobre eventual "
            "disputa jurídica decorrente.",
            styles["CorpoDoc"],
        ),
    ]
    _doc("regimento_carregamento_compartilhado.pdf", "Regimento Interno — Carregamento Compartilhado de Veículos Elétricos", el)


def gerar_faq() -> None:
    perguntas = [
        (
            "Quanto tempo leva para carregar completamente meu veículo?",
            "Depende da potência aceita pelo veículo e da potência entregue pelo "
            "carregador. No ChargeGrid HCA G2, em modo trifásico (até 22 kW), a maioria "
            "dos veículos de passeio com bateria de 40-60 kWh atinge carga completa "
            "entre 2 e 3 horas, partindo de um nível baixo de carga. Em modo "
            "monofásico (7,4 kW), o tempo é proporcionalmente maior.",
        ),
        (
            "Posso ver quanto já foi gasto na sessão atual antes de ela terminar?",
            "Sim, a energia entregue (kWh) e o valor faturado (BRL) são atualizados em "
            "tempo real durante a sessão e podem ser consultados a qualquer momento "
            "pelo aplicativo ou pelo assistente virtual, mesmo com a sessão ainda em "
            "andamento (estado 'Em carga').",
        ),
        (
            "O que fazer se o carregador aparecer como 'Offline'?",
            "'Offline' indica perda de comunicação do carregador com a plataforma EV "
            "ChargeOps (geralmente problema de rede Wi-Fi/Ethernet local), não "
            "necessariamente uma falha do carregador em si. Uma sessão em andamento "
            "continua normalmente mesmo offline; os dados são sincronizados assim que "
            "a conexão voltar. Se o problema persistir por mais de algumas horas, "
            "verificar a rede local antes de acionar a assistência técnica.",
        ),
        (
            "É seguro deixar o carregador carregando durante a noite sem supervisão?",
            "Sim — o ChargeGrid HCA G2 tem proteção diferencial (RCD Tipo B) e monitora "
            "continuamente a sessão, interrompendo automaticamente o carregamento em "
            "caso de falha (estado 'Em falha'). Ainda assim, a instalação elétrica "
            "correta (feita por eletricista certificado) é pré-requisito para essa "
            "segurança funcionar como projetado.",
        ),
        (
            "Posso usar o carregador de um condomínio vizinho ou emprestar minha vaga para visitante?",
            "O uso dos pontos de recarga da garagem compartilhada é restrito às "
            "unidades cadastradas no sistema do próprio condomínio, conforme o "
            "regimento de carregamento compartilhado — empréstimo de vaga ou acesso "
            "por terceiros não cadastrados deve ser tratado diretamente com a "
            "administração do condomínio.",
        ),
        (
            "Por que a potência entregue às vezes é menor que os 22 kW máximos do carregador?",
            "A potência efetiva de uma sessão é limitada pelo menor valor entre: a "
            "capacidade máxima do carregador (22 kW trifásico), a capacidade máxima do "
            "carregador de bordo do veículo (varia por modelo) e a disponibilidade da "
            "instalação elétrica do local. É normal e esperado a potência entregue "
            "ficar abaixo do teto do carregador dependendo do veículo conectado.",
        ),
    ]

    el = [Paragraph("Perguntas frequentes — Carregamento GoodWe", styles["H1Doc"])]
    for pergunta, resposta in perguntas:
        el.append(Paragraph(f"P: {pergunta}", styles["H2Doc"]))
        el.append(Paragraph(f"R: {resposta}", styles["CorpoDoc"]))

    _doc("faq_carregamento.pdf", "FAQ — Carregamento de Veículos Elétricos GoodWe", el)


def gerar_tabela_tarifaria() -> None:
    el = [
        Paragraph("1. Tarifa de energia por posto de recarga", styles["H1Doc"]),
        Paragraph(
            "Valores aplicados ao faturamento de sessões de recarga nos pontos "
            "gerenciados pela plataforma EV ChargeOps, vigentes a partir da data de "
            "publicação deste documento. Tarifas diferenciadas por faixa horária "
            "incentivam o carregamento fora do horário de pico da rede elétrica.",
            styles["CorpoDoc"],
        ),
        _tabela(
            [
                ["Faixa horária", "Horário", "Tarifa (R$/kWh)"],
                ["Ponta", "18h às 21h", "R$ 1,20"],
                ["Intermediário", "6h às 18h e 21h às 23h", "R$ 0,85"],
                ["Fora de ponta (noturno)", "23h às 6h", "R$ 0,55"],
            ],
            largura_primeira_col=5.0,
        ),
        Spacer(1, 10),
        Paragraph("2. Taxas adicionais", styles["H1Doc"]),
        _tabela(
            [
                ["Item", "Descrição", "Valor"],
                ["Taxa de manutenção mensal", "Rateada entre unidades cadastradas (ver regimento, seção 3)", "R$ 12,00 por unidade cadastrada"],
                ["Taxa de ociosidade", "Cobrada por minuto quando o veículo permanece conectado após o fim da sessão (estado 'Concluído') além do prazo de 30 minutos previsto no regimento", "R$ 0,50/minuto após a tolerância"],
            ],
            largura_primeira_col=4.5,
        ),
        Spacer(1, 10),
        Paragraph("3. Reajuste", styles["H1Doc"]),
        Paragraph(
            "Os valores desta tabela são revisados anualmente pela administração do "
            "condomínio em conjunto com a concessionária de energia local, e "
            "comunicados aos condôminos com 30 dias de antecedência. Este assistente "
            "não tem autoridade para alterar, prever ou negociar os valores tarifários "
            "— apenas informar a tabela vigente registrada nesta base.",
            styles["CorpoDoc"],
        ),
    ]
    _doc("tabela_tarifaria.pdf", "Tabela Tarifária — Carregamento de Veículos Elétricos", el)


def main() -> None:
    gerar_manual_chargegrid()
    gerar_regimento_condominial()
    gerar_faq()
    gerar_tabela_tarifaria()
    print("\n4 PDFs gerados em data/knowledge_base/. Rode `python -m src.rag.indexar` para indexar.")


if __name__ == "__main__":
    main()
