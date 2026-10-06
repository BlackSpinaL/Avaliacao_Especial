import streamlit as st
import pandas as pd

st.set_page_config(page_title="Avaliação Especial", layout="wide")

st.title("🔒 Cálculo de Solicitações de Avaliação Especial - Acesso Restrito")

# ✅ Instruções exibidas antes do upload
st.markdown(
    """
    ### 📋 Instruções antes de enviar a planilha
    1. **Retirar as 2 primeiras linhas** da planilha;
    2. **Descongelar as linhas** (caso estejam congeladas);
    3. **Salvar e enviar** o arquivo no campo abaixo.
    """
)

st.divider()  # opcional: linha divisória para separar visualmente

# Lista de matrículas autorizadas
matriculas_autorizadas = ["1547215", "1610344", "1674159"]

# Tela de login por matrícula
matricula = st.text_input("Digite sua matrícula para acessar:")

if matricula in matriculas_autorizadas:
    st.success("Acesso liberado!")

    uploaded_file = st.file_uploader("Envie o arquivo de solicitações (Excel)", type=["xlsx"])

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
            df_long = df_long.drop_duplicates(subset=["Matrícula", "Disciplina", "Tipo"])
        else:
            st.error(f"Colunas encontradas: {df.columns.tolist()}")
            st.stop()

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

        resultado = filtrado.pivot_table(
            index="Disciplina",
            columns="Tipo",
            values="Matrícula",
            aggfunc="count",
            fill_value=0
        ).reset_index()

        resultado["Total Geral"] = resultado.sum(axis=1, numeric_only=True)

        totais_situacao = filtrado.groupby("Tipo").size().reset_index(name="Total")

        total_geral = filtrado.shape[0]

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
    if matricula:
        st.error("Matrícula não autorizada. Contate o administrador.")
