import streamlit as st
import pandas as pd
import io
import os

st.set_page_config(page_title="Avaliação Especial", layout="wide")

st.title("🔒 Cálculo de Solicitações de Avaliação Especial - Acesso Restrito")

# Lista de matrículas autorizadas
matriculas_autorizadas = ["1547215", "1610344", "1674159"]

# Tela de login por matrícula
matricula = st.text_input("Digite sua matrícula para acessar:")

if matricula in matriculas_autorizadas:
    st.success("Acesso liberado!")

    # ============================================================
    # TUTORIAL DE UPLOAD (Baseado no modelo enviado)
    # ============================================================
    st.header("1️⃣ Tutorial de Envio da Planilha")
    st.caption("Fluxo: 1️⃣ faça login ➔ 2️⃣ envie a planilha ➔ 3️⃣ selecione os filtros ➔ 4️⃣ visualize os resultados.")

    st.warning(
        "⚠️ **ATENÇÃO** — A planilha deve conter **SOMENTE** as colunas do modelo abaixo. "
        "Colunas extras (filtros, observações, notas antigas, etc.) podem atrapalhar o processamento."
    )

    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.markdown("**Modelo correto (exemplo):**")
        
        # Criando um DataFrame de exemplo visual para o usuário
        dados_exemplo = [
            ["000000", "AAAAA AAAAA AAAAA", "12101", "ENSINO MÉDIO", 2026, 1, "021 - BIOLOGIA", "RECUPERACAO", "027 - QUIMICA", "RECUPERACAO", "026 - FISICA", "RECUPERACAO", "017 - MATEMATICA", "RECUPERACAO"],
            ["111111", "BBBBB BBBBB BBBBB", "12102", "ENSINO MÉDIO", 2026, 1, "021 - BIOLOGIA", "RECUPERACAO", "009 - GEOGRAFIA", "RECUPERACAO", "", "", "", ""]
        ]
        colunas_exemplo = [
            "Matrícula", "Nome do Aluno", "Código Turma", "Curso", "Ano Letivo", "Etapa", 
            "1ª Disciplina", "Motivo", "2ª Disciplina", "Motivo", "3ª Disciplina", "Motivo", "4ª Disciplina", "Motivo"
        ]
        exemplo_df = pd.DataFrame(dados_exemplo, columns=colunas_exemplo)
        st.dataframe(exemplo_df, use_container_width=True)

        # Botão para baixar a planilha modelo em branco
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            template_df = pd.DataFrame(columns=colunas_exemplo)
            template_df.to_excel(writer, index=False)
        
        st.download_button(
            label="📥 Baixar planilha-modelo (.xlsx)",
            data=buffer.getvalue(),
            file_name="modelo_avaliacao_especial.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col2:
        st.markdown("**Colunas obrigatórias:**")
        st.markdown(
            "- `Matrícula`\n"
            "- `Nome do Aluno`\n"
            "- `Código Turma`\n"
            "- `Curso`\n"
            "- `Ano Letivo`\n"
            "- `Etapa`\n"
            "- Pelo menos uma coluna de disciplina (`1ª Disciplina`, `2ª Disciplina`, ...) e seu respectivo `Motivo`"
        )
        st.markdown("**Formato da disciplina:** `código - NOME` (ex.: `017 - MATEMATICA`)")
        st.markdown("Remova da planilha qualquer coluna que não esteja no modelo — inclusive filtros e colunas em branco no final.")

    st.divider()
    # ============================================================

    st.subheader("Envie o arquivo Excel com as solicitações")
    uploaded_file = st.file_uploader("Faça o upload da planilha", type=["xlsx"])

    if uploaded_file:
        df = pd.read_excel(uploaded_file)

        disciplina_cols = [col for col in df.columns if "Disciplina" in col]
        motivo_cols = [col for col in df.columns if "Motivo" in col]

        disciplinas = []
        for i, col_disc in enumerate(disciplina_cols):
            if i < len(motivo_cols):
                col_motivo = motivo_cols[i]
                temp = df[[
                    "Matrícula", "Nome do Aluno", "Código Turma",
                    "Curso", "Ano Letivo", "Etapa", col_disc, col_motivo
                ]].copy()
                temp = temp.rename(columns={col_disc: "Disciplina", col_motivo: "Tipo"})
                temp = temp[temp["Disciplina"].notna()]
                disciplinas.append(temp)

        if disciplinas:
            df_long = pd.concat(disciplinas)
            # Remove duplicatas de solicitações do mesmo aluno na mesma disciplina e tipo
            df_long = df_long.drop_duplicates(subset=["Matrícula", "Disciplina", "Tipo"])
        else:
            st.error(f"Colunas encontradas: {df.columns.tolist()}")
            st.stop()

        # Filtros com opções ordenadas
        col1, col2, col3 = st.columns(3)
        with col1:
            turmas = st.multiselect(
                "Selecione as turmas",
                sorted(df_long["Código Turma"].unique())
            )
        with col2:
            segmentos = st.multiselect(
                "Selecione os segmentos",
                sorted(df_long["Curso"].unique())
            )
        with col3:
            tipo = st.selectbox("Tipo de avaliação", ["Todos", "RECUPERACAO", "MELHORIA DE NOTA"])

        filtrado = df_long.copy()
        if turmas:
            filtrado = filtrado[filtrado["Código Turma"].isin(turmas)]
        if segmentos:
            filtrado = filtrado[filtrado["Curso"].isin(segmentos)]
        if tipo != "Todos":
            filtrado = filtrado[filtrado["Tipo"] == tipo]

        # Consolidar em uma linha por disciplina
        resultado = filtrado.pivot_table(
            index="Disciplina",
            columns="Tipo",
            values="Matrícula",
            aggfunc="count",
            fill_value=0
        ).reset_index()

        # Adicionar coluna de total geral por disciplina
        resultado["Total Geral"] = resultado.sum(axis=1, numeric_only=True)

        # Totais por situação
        totais_situacao = filtrado.groupby("Tipo").size().reset_index(name="Total")

        # Total geral
        total_geral = filtrado.shape[0]

        # Mostrar resultados com cabeçalhos centralizados
        st.subheader("Resultados filtrados")
        st.dataframe(resultado.style.set_table_styles(
            [{'selector': 'th', 'props': [('text-align', 'center')]}]
        ))

        st.subheader("Totais por situação (Melhoria ou Recuperação)")
        st.dataframe(totais_situacao.style.set_table_styles(
            [{'selector': 'th', 'props': [('text-align', 'center')]}]
        ))

        st.metric("TOTAL GERAL", total_geral)

        st.subheader("Gráfico por disciplina")
        if not resultado.empty:
            st.bar_chart(resultado.set_index("Disciplina")["Total Geral"])
        else:
            st.info("Nenhum dado encontrado para os filtros selecionados.")

else:
    if matricula:  # só mostra erro se o usuário digitou algo
        st.error("Matrícula não autorizada. Contate o administrador.")
