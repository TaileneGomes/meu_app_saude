from flask import Flask, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

# Configurações do MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'  # Usuário do MySQL (geralmente root por padrão)
app.config['MYSQL_PASSWORD'] = ''   # Senha do MySQL (normalmente vazia por padrão)
app.config['MYSQL_DB'] = 'meu_app_flask'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

# Rotas do Flask
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/contato', methods=['GET', 'POST'])
def contato():
    if request.method == 'POST':
        nome = request.form['nome']
        endereco = request.form['endereco']
        email = request.form['email']
        telefone = request.form['telefone']
        mensagem = request.form['mensagem']

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO contatos (nome, endereco, email, telefone, mensagem) VALUES (%s, %s, %s, %s, %s)",
                    (nome, endereco, email, telefone, mensagem))
        mysql.connection.commit()
        cur.close()

        flash('Mensagem enviada com sucesso!', 'success')
        return redirect(url_for('index'))

    return render_template('contato.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/cadastro', methods=['POST'])
def cadastro():
    nome = request.form['nome']
    endereco = request.form['endereco']
    email = request.form['email']
    telefone = request.form['telefone']
    senha = request.form['senha']

    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO usuarios (nome, endereco, email, telefone, senha) VALUES (%s, %s, %s, %s, %s)",
                (nome, endereco, email, telefone, senha))
    mysql.connection.commit()
    cur.close()

    flash('Cadastro realizado com sucesso!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
