import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

# BANCO DE DADOS
class BancoDeDados:
    def __init__(self):
        self.conn = sqlite3.connect("contatos.db")
        self.cursor = self.conn.cursor()
        self._criar_tabela()

    def _criar_tabela(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS contatos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                numero TEXT NOT NULL,
                categoria TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def adicionar(self, nome, numero, categoria):
        self.cursor.execute(
            "INSERT INTO contatos (nome, numero, categoria) VALUES (?, ?, ?)",
            (nome, numero, categoria)
        )
        self.conn.commit()

    def listar(self):
        self.cursor.execute("SELECT id, nome, numero, categoria FROM contatos")
        return self.cursor.fetchall()

    def pesquisar(self, termo):
        termo = f"%{termo}%"
        self.cursor.execute("""
            SELECT id, nome, numero, categoria FROM contatos
            WHERE nome LIKE ? OR numero LIKE ?
        """, (termo, termo))
        return self.cursor.fetchall()

    def atualizar(self, id_contato, nome, numero, categoria):
        self.cursor.execute("""
            UPDATE contatos 
            SET nome=?, numero=?, categoria=? 
            WHERE id=?
        """, (nome, numero, categoria, id_contato))
        self.conn.commit()

    def excluir(self, id_contato):
        self.cursor.execute("DELETE FROM contatos WHERE id=?", (id_contato,))
        self.conn.commit()


# APLICAÇÃO TKINTER
class AgendaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Agenda de Contatos")
        self.db = BancoDeDados()

        self.contato_selecionado = None  # guarda o ID interno

        self._criar_interface()
        self._carregar_contatos()

    # INTERFACE
    def _criar_interface(self):

        # --- Labels e Inputs ---
        tk.Label(self.root, text="Nome:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.entry_nome = ttk.Entry(self.root, width=40)
        self.entry_nome.grid(row=0, column=1, pady=5)

        tk.Label(self.root, text="Número:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.entry_numero = ttk.Entry(self.root, width=40, validate="key")
        self.entry_numero['validatecommand'] = (self.root.register(self._validar_numeros), "%P")
        self.entry_numero.grid(row=1, column=1, pady=5)

        tk.Label(self.root, text="Categoria:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.combo_categoria = ttk.Combobox(self.root, values=["Pessoal", "Profissional"], state="readonly")
        self.combo_categoria.grid(row=2, column=1, pady=5)
        self.combo_categoria.set("Pessoal")

        # --- Botões ---
        ttk.Button(self.root, text="Adicionar", command=self.adicionar).grid(row=3, column=0, pady=10)
        ttk.Button(self.root, text="Editar", command=self.editar).grid(row=3, column=1, sticky="w", padx=80)
        ttk.Button(self.root, text="Excluir", command=self.excluir).grid(row=3, column=1, sticky="e", padx=10)

        # --- Campo de Pesquisa ---
        tk.Label(self.root, text="Pesquisar (nome ou número):").grid(row=4, column=0, sticky="w", padx=10)
        self.entry_pesquisa = ttk.Entry(self.root, width=40)
        self.entry_pesquisa.grid(row=4, column=1, pady=5)

        ttk.Button(self.root, text="Buscar", command=self.pesquisar).grid(row=5, column=0, pady=5)
        ttk.Button(self.root, text="Limpar busca", command=self._carregar_contatos).grid(row=5, column=1, sticky="w")

        # --- Tabela ---
        colunas = ("nome", "numero", "categoria")
        self.tabela = ttk.Treeview(self.root, columns=colunas, show="headings", height=12)

        self.tabela.heading("nome", text="Nome")
        self.tabela.heading("numero", text="Número")
        self.tabela.heading("categoria", text="Categoria")

        self.tabela.column("nome", width=180)
        self.tabela.column("numero", width=140)
        self.tabela.column("categoria", width=120)

        self.tabela.grid(row=6, column=0, columnspan=2, padx=10, pady=10)
        self.tabela.bind("<<TreeviewSelect>>", self._selecionar)

    # VALIDAÇÃO
    def _validar_numeros(self, texto):
        return texto.isdigit() or texto == ""

    # FUNÇÕES PRINCIPAIS
    def adicionar(self):
        nome = self.entry_nome.get().strip()
        numero = self.entry_numero.get().strip()
        categoria = self.combo_categoria.get()

        if not nome:
            messagebox.showerror("Erro", "Digite um nome.")
            return
        if not numero:
            messagebox.showerror("Erro", "Digite um número.")
            return

        self.db.adicionar(nome, numero, categoria)
        self._carregar_contatos()
        self._limpar()

    def editar(self):
        if not self.contato_selecionado:
            messagebox.showwarning("Aviso", "Selecione um contato para editar.")
            return

        nome = self.entry_nome.get().strip()
        numero = self.entry_numero.get().strip()
        categoria = self.combo_categoria.get()

        self.db.atualizar(self.contato_selecionado, nome, numero, categoria)
        self._carregar_contatos()
        self._limpar()

    def excluir(self):
        if not self.contato_selecionado:
            messagebox.showwarning("Aviso", "Selecione um contato para excluir.")
            return

        self.db.excluir(self.contato_selecionado)
        self._carregar_contatos()
        self._limpar()

    # PESQUISAR
    def pesquisar(self):
        termo = self.entry_pesquisa.get().strip()
        if not termo:
            messagebox.showinfo("Aviso", "Digite algo para pesquisar.")
            return

        resultados = self.db.pesquisar(termo)

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for contato in resultados:
            contato_id, nome, numero, categoria = contato
            self.tabela.insert("", tk.END, iid=contato_id, values=(nome, numero, categoria))

    # AUXILIARES
    def _carregar_contatos(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for contato in self.db.listar():
            contato_id, nome, numero, categoria = contato
            self.tabela.insert("", tk.END, iid=contato_id, values=(nome, numero, categoria))

    def _selecionar(self, event):
        selecionado = self.tabela.selection()
        if not selecionado:
            return

        contato_id = int(selecionado[0])
        self.contato_selecionado = contato_id

        valores = self.tabela.item(contato_id, "values")
        nome, numero, categoria = valores

        self.entry_nome.delete(0, tk.END)
        self.entry_nome.insert(0, nome)

        self.entry_numero.delete(0, tk.END)
        self.entry_numero.insert(0, numero)

        self.combo_categoria.set(categoria)

    def _limpar(self):
        self.entry_nome.delete(0, tk.END)
        self.entry_numero.delete(0, tk.END)
        self.combo_categoria.set("Pessoal")
        self.contato_selecionado = None

# INÍCIO DO PROGRAMA
if __name__ == "__main__":
    root = tk.Tk()
    AgendaApp(root)
    root.mainloop()
