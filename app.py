from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
from flask_mysqldb import MySQL
from io import BytesIO
from reportlab.pdfgen import canvas
from xlsxwriter.workbook import Workbook

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

# Configurações do MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Usuário do MySQL (geralmente root por padrão)
app.config['MYSQL_PASSWORD'] = ''   # Senha do MySQL (normalmente vazia por padrão)
app.config['MYSQL_DB'] = 'meu_app_flask'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Rota da página inicial
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE username = %s AND senha = %s", (username, senha))
        usuario = cur.fetchone()
        cur.close()

        if usuario:
            session['usuario'] = usuario
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('profissionais'))  # Redireciona para a página de profissionais
        else:
            flash('Usuário ou senha incorretos. Por favor, tente novamente.', 'danger')

    return render_template('index.html')

# Rota da página Sobre
@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

# Rota da página de contato
@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        nome = request.form['nome']
        endereco = request.form['endereco']
        email = request.form['email']
        telefone = request.form['telefone']
        mensagem = request.form['mensagem']

        # Obtém o ID do usuário logado
        if 'usuario' in session:
            usuario_id = session['usuario']['id']
        else:
            usuario_id = None

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO contatos (nome, endereco, email, telefone, mensagem, usuario_id) VALUES (%s, %s, %s, %s, %s, %s)",
                    (nome, endereco, email, telefone, mensagem, usuario_id))
        mysql.connection.commit()
        cur.close()

        flash('Mensagem enviada com sucesso!', 'success')
        return redirect(url_for('index'))

    return render_template('contato.html')

# Rota para cadastro de novos usuários
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        endereco = request.form['endereco']
        email = request.form['email']
        telefone = request.form['telefone']
        coren_rs = request.form['coren_rs']
        username = request.form['username']
        senha = request.form['senha']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO usuarios (nome, endereco, email, telefone, coren_rs, username, senha) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (nome, endereco, email, telefone, coren_rs, username, senha))
        mysql.connection.commit()
        cur.close()

        flash('Cadastro realizado com sucesso!', 'success')
        return redirect(url_for('index'))

    return render_template('cadastro.html')

# Rota para exibir profissionais cadastrados
@app.route('/profissionais')
def profissionais():
    # Verifica se há um usuário na sessão
    if 'usuario' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT *, ROUND(AVG(avaliacoes.nota), 1) AS media_notas, GROUP_CONCAT(avaliacoes.comentario SEPARATOR '<br>') AS comentarios FROM usuarios LEFT JOIN avaliacoes ON usuarios.id = avaliacoes.profissional_id GROUP BY usuarios.id")
        profissionais = cur.fetchall()
        cur.close()

        return render_template('profissionais.html', profissionais=profissionais, usuario=session['usuario'])
    else:
        flash('Faça login para acessar esta página.', 'warning')
        return redirect(url_for('index'))

# Rota para realizar logout
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('index'))

# Rota para avaliar um profissional
@app.route('/avaliar_profissional/<int:profissional_id>', methods=['POST'])
def avaliar_profissional(profissional_id):
    if 'usuario' in session:
        nota = request.form['nota']
        comentario = request.form['comentario']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO avaliacoes (profissional_id, nota, comentario) VALUES (%s, %s, %s)",
                    (profissional_id, nota, comentario))
        mysql.connection.commit()
        cur.close()

        flash('Avaliação enviada com sucesso!', 'success')
    else:
        flash('Faça login para acessar esta página.', 'warning')

    return redirect(url_for('profissionais'))

# Rota para editar um profissional
@app.route('/editar_profissional/<int:profissional_id>', methods=['GET', 'POST'])
def editar_profissional(profissional_id):
    if 'usuario' in session:
        if request.method == 'POST':
            nome = request.form['nome']
            endereco = request.form['endereco']
            email = request.form['email']
            telefone = request.form['telefone']
            coren_rs = request.form['coren_rs']
            username = request.form['username']
            senha = request.form['senha']

            cur = mysql.connection.cursor()
            cur.execute("""
                UPDATE usuarios 
                SET nome = %s, endereco = %s, email = %s, telefone = %s, coren_rs = %s, username = %s, senha = %s
                WHERE id = %s
            """, (nome, endereco, email, telefone, coren_rs, username, senha, profissional_id))
            mysql.connection.commit()
            cur.close()

            flash('Dados do profissional atualizados com sucesso!', 'success')
            return redirect(url_for('profissionais'))

        # Busca o profissional pelo ID para preencher o formulário de edição
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios WHERE id = %s", (profissional_id,))
        profissional = cur.fetchone()
        cur.close()

        return render_template('editar_profissional.html', profissional=profissional)
    else:
        flash('Faça login para acessar esta página.', 'warning')
        return redirect(url_for('index'))

# Rota para excluir um profissional
@app.route('/excluir_profissional/<int:profissional_id>', methods=['POST','GET'])
def excluir_profissional(profissional_id):
    if 'usuario' in session:
        try:
            print(profissional_id)
            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM usuarios WHERE id = %s", (profissional_id,))
            mysql.connection.commit()
            cur.close()

            flash('Profissional excluído com sucesso!', 'success')
        except Exception as e:
            flash(f"Erro ao excluir o profissional: {str(e)}", 'danger')

        return redirect(url_for('profissionais'))
    else:
        flash('Faça login para acessar esta página.', 'warning')
        return redirect(url_for('index'))

# Rota para gerar relatório em PDF
@app.route('/gerar_pdf')
def gerar_pdf():
    if 'usuario' in session:
        # Cria um buffer de memória para o PDF
        buffer = BytesIO()

        # Gera o conteúdo do PDF
        c = canvas.Canvas(buffer)
        c.drawString(100, 750, "Relatório de Profissionais")
        c.drawString(100, 730, "--------------------------------------------")

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios")
        profissionais = cur.fetchall()
        y = 700
        for profissional in profissionais:
            c.drawString(100, y, f"Nome: {profissional['nome']}")
            c.drawString(100, y - 20, f"Email: {profissional['email']}")
            c.drawString(100, y - 40, f"Telefone: {profissional['telefone']}")
            c.drawString(100, y - 60, "--------------------------------------------")
            y -= 80

        c.save()

        # Define o buffer para o início
        buffer.seek(0)

        # Retorna a resposta do PDF
        return Response(buffer, mimetype='application/pdf')
    else:
        flash('Faça login para acessar esta página.', 'warning')
        return redirect(url_for('index'))

# Rota para gerar relatório em Excel
@app.route('/gerar_excel')
def gerar_excel():
    if 'usuario' in session:
        # Cria um buffer de memória para o Excel
        buffer = BytesIO()

        # Cria um novo workbook no Excel
        workbook = Workbook(buffer, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Escreve os cabeçalhos
        worksheet.write(0, 0, 'Nome')
        worksheet.write(0, 1, 'Email')
        worksheet.write(0, 2, 'Telefone')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM usuarios")
        profissionais = cur.fetchall()

        row = 1
        for profissional in profissionais:
            worksheet.write(row, 0, profissional['nome'])
            worksheet.write(row, 1, profissional['email'])
            worksheet.write(row, 2, profissional['telefone'])
            row += 1

        workbook.close()

        # Define o buffer para o início
        buffer.seek(0)

        # Retorna a resposta do Excel
        return Response(buffer, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        flash('Faça login para acessar esta página.', 'warning')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
