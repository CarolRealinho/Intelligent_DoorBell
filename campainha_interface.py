import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QLineEdit, QComboBox,  QMessageBox
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QFileDialog
from PyQt5.QtCore import QUrl, Qt, QThread
from PyQt5.QtGui import QIcon
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
import serial
import time
import re

import numpy as np
import face_recognition
import os
from PIL import Image, ImageDraw, ImageFont
import sounddevice as sd
from arduino import Arduino

"""
Este programa implementa uma aplicação de campainha inteligente usando PyQt5 para a interface gráfica do 
utilizador (GUI). O programa permite ao utilizador configurar uma campainha inteligente que envia notificações 
por e-mail quando acionada. Ele também oferece recursos como seleção de som de campainha, envio de mensagens 
personalizadas e autenticação por reconhecimento facial.

Requisitos:
    - Python 3.x
    - PyQt5
    - NumPy
    - face_recognition
    - Pillow
    - sounddevice
    - pyserial

Além disso, o programa requer acesso à internet para enviar e-mails e acesso a uma porta serial para 
comunicar com a campainha.

O programa possui várias funcionalidades, incluindo:
    - Configuração inicial com autenticação.
    - Reconhecimento facial do visitante.
    - Seleção de som de campainha.
    - Envio de mensagens personalizadas.
    - Notificação por e-mail quando a campainha é acionada.
    - Ativação e desativação da campainha.

Nota: Este programa requer o fornecimento de credenciais de e-mail para enviar notificações.
"""

class MainWindow(QMainWindow):
    """Classe da janela principal para o aplicativo Campainha Inteligente.

    Esta classe implementa a interface gráfica do usuário e a funcionalidade principal
    do aplicativo Campainha Inteligente. Ela fornece recursos como autenticação de usuário,
    configuração das configurações da campainha e envio de notificações por e-mail.

    Atributos:
        ToqueSelecionado (str): Armazena o som da campainha selecionado.
        serial (serial.Serial): Objeto de comunicação serial com o dispositivo Arduino.
        link (str): URL para a imagem da câmera da campainha.
    """
    def __init__(self):
        """Inicializa a janela principal."""
        super().__init__()
        self.ToqueSelecionado = None # inicializa uma variável para armazenar o toque selecionado
        self.setWindowTitle("Campainha inteligente") # define o título da janela como "Campainha inteligente"
           
        nome_porta = '' # inicializa uma variável para armazenar o nome da porta
        for porta in ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2']:
            if os.path.exists(porta): # verifica se a porta existe no sistema operacional
                nome_porta = porta # armazena o nome da porta serial encontrada
                break # interrompe o loop assim que uma porta válida é encontrada

        if not nome_porta: # verifica se nenhuma porta válida foi encontrada
            print("Erro. Arduino não conectado!") # mensagem de erro que indica que o Arduino não está conectado
            sys.exit(1) # encerra o programa com código de erro 1
            
        self.serial = serial.Serial(nome_porta, 9600) # inicializa a comunicação serial com o Arduino
        time.sleep(2)  # delay para permitir que o Arduino seja reiniciado
         
        self.link = "http://192.168.126.112/cam-hi.jpg" # define o link para a imagem da câmera
        self.initUI() # inicializa a interface do usuário


    def initUI(self):
        """Inicializa a interface do utilizador."""
        # Cria um novo widget central
        self.centralWidget = QWidget()
        # Define o widget central da janela como o widget recém-criado
        self.setCentralWidget(self.centralWidget)
        # Cria um layout vertical para organizar os widgets dentro do widget central
        self.stackedLayout = QVBoxLayout(self.centralWidget)
      
        # Título da primeira página
        self.TituloPag1 = QLabel("Bem-vinde à campainha inteligente", self)
        # Centraliza o texto do título
        self.TituloPag1.setAlignment(Qt.AlignCenter)
        # Adiciona o título ao layout vertical
        self.stackedLayout.addWidget(self.TituloPag1)

        # Campo de entrada para o nome de usuário
        self.NomeInserido = QLineEdit(self)
        # Define um texto de placeholder para indicar o que deve ser introduzido no campo
        self.NomeInserido.setPlaceholderText("Insira o seu username:")
        # Adiciona o campo de entrada ao layout vertical
        self.stackedLayout.addWidget(self.NomeInserido)

        # Campo de entrada para a palavra-passe
        self.PalavraChave = QLineEdit(self)
        # Define um texto de placeholder para indicar o que deve ser introduzido no campo
        self.PalavraChave.setPlaceholderText("Insira a sua password:")
        # Configura o modo de eco para ocultar os caracteres digitados
        self.PalavraChave.setEchoMode(QLineEdit.Password)
        # Adiciona o campo de entrada ao layout vertical
        self.stackedLayout.addWidget(self.PalavraChave)

        # Botão para fazer upload de uma imagem do dono
        self.botao_carregar_imagem = QPushButton('Dê upload da sua imagem', self)
        # Conecta o clique do botão ao método uploadGuardarFoto
        self.botao_carregar_imagem.clicked.connect(self.uploadGuardarFoto)
        # Adiciona o botão ao layout vertical
        self.stackedLayout.addWidget(self.botao_carregar_imagem)
        # Texto que indica se a foto foi selecionada
        self.FotoSelecionada = QLabel("Nenhuma foto selecionada", self)
        # Adiciona a label ao layout vertical
        self.stackedLayout.addWidget(self.FotoSelecionada)
        
        # Botão para iniciar sessão
        self.Botao_Iniciar = QPushButton("Iniciar", self)
        # Conecta o clique do botão ao método verificarCredenciais
        self.Botao_Iniciar.clicked.connect(self.verificarCredenciais)
        # Adiciona o botão ao layout vertical
        self.stackedLayout.addWidget(self.Botao_Iniciar)
        
        # Título da segunda página
        self.TituloPag2 = QLabel("Configuração da campainha", self)
        # Adiciona a label ao layout vertical
        self.stackedLayout.addWidget(self.TituloPag2)
        # Oculta o título da segunda página inicialmente
        self.TituloPag2.hide()

        # Label de instrução para escolher um som
        self.SelecionarSom = QLabel(" \u25BA Por favor, escolha uma campainha:", self)
        # Adiciona a label ao layout vertical
        self.stackedLayout.addWidget(self.SelecionarSom)
        # Oculta o título inicialmente
        self.SelecionarSom.hide()
        
        # Caixa de combinação para selecionar o som
        self.CaixaComboCampainha = QComboBox(self)
        # Adiciona os itens à caixa de combinação
        self.CaixaComboCampainha.addItems(["Selecione o Ringtone", "Ringtone 1", "Ringtone 2", "Ringtone 3"])
        # Conecta a mudança de seleção à função atualizarCampainha
        self.CaixaComboCampainha.currentIndexChanged.connect(self.atualizarCampainha)
        # Adiciona a caixa de combinação ao layout vertical
        self.stackedLayout.addWidget(self.CaixaComboCampainha)
        # Oculta a caixa de combinação inicialmente
        self.CaixaComboCampainha.hide()
        
        # Label para exibir a campainha selecionada
        self.CampainhaSelecionada = QLabel("", self)
        # Adiciona a label ao layout vertical
        self.stackedLayout.addWidget(self.CampainhaSelecionada)
        # Oculta a label inicialmente
        self.CampainhaSelecionada.hide()
        
        # Label de instrução para escolher uma mensagem para o display
        self.mendisplay = QLabel(" \u25BA Escolha uma mensagem para deixar no display:", self)
        # Adiciona a label ao layout vertical
        self.stackedLayout.addWidget(self.mendisplay)
        # Oculta a label inicialmente
        self.mendisplay.hide()
        # Campo de entrada para a mensagem do display
        self.mensagemDisplay = QLineEdit(self)
        # Define um texto de placeholder para indicar o que deve ser digitado no campo
        self.mensagemDisplay.setPlaceholderText("Insira texto até 150 caracteres")
        # Adiciona o campo de entrada ao layout vertical
        self.stackedLayout.addWidget(self.mensagemDisplay)
        # Oculta o campo de entrada inicialmente
        self.mensagemDisplay.hide()
        # Botão para confirmar a mensagem
        self.Botao_mensagem = QPushButton("OK", self)
        # Conecta o clique do botão ao método mensagem
        self.Botao_mensagem.clicked.connect(self.mensagem)
        # Adiciona o botão ao layout vertical
        self.stackedLayout.addWidget(self.Botao_mensagem)
        # Oculta o botão inicialmente
        self.Botao_mensagem.hide()
        
        # Texto de instrução para escolher o e-mail para notificação
        self.emaildisplay = QLabel(" \u25BA Escolha email no qual quer ser notificado:", self)
        # Adiciona a label ao layout vertical
        self.stackedLayout.addWidget(self.emaildisplay)
        # Oculta a label inicialmente
        self.emaildisplay.hide()
        # Campo de entrada para o endereço de e-mail
        self.emailUtilizador = QLineEdit(self)
        # Define um texto de placeholder para indicar o que deve ser digitado no campo
        self.emailUtilizador.setPlaceholderText("Insira email")
        # Adiciona o campo de entrada ao layout vertical
        self.stackedLayout.addWidget(self.emailUtilizador)
        # Oculta o campo de entrada inicialmente
        self.emailUtilizador.hide()
        # Botão para verificar os campos e avançar
        self.Botao_Verificar_Campos = QPushButton("Verificar Campos e Avançar", self)
        # Conecta o clique do botão ao método verificaCamposAvancar
        self.Botao_Verificar_Campos.clicked.connect(self.verificaCamposAvancar)
        # Adiciona o botão ao layout vertical
        self.stackedLayout.addWidget(self.Botao_Verificar_Campos)
        # Oculta o botão inicialmente
        self.Botao_Verificar_Campos.hide()
        # Botão para voltar à página anterior
        self.Botao_Voltar_Atras = QPushButton("Voltar", self)
        # Conecta o clique do botão ao método mudarParaPag1
        self.Botao_Voltar_Atras.clicked.connect(self.mudarParaPag1)
        # Adiciona o botão ao layout vertical
        self.stackedLayout.addWidget(self.Botao_Voltar_Atras)
        # Oculta o botão inicialmente
        self.Botao_Voltar_Atras.hide()

        # Texto da terceira página
        self.TituloPag3 = QLabel("Campainha inteligente ativada", self)
        # Adiciona a label ao layout vertical
        self.stackedLayout.addWidget(self.TituloPag3)
        # Oculta a label inicialmente
        self.TituloPag3.hide()
        # Botão para configurações avançadas
        self.Botao_opcoes_avancadas = QPushButton("Configurações Avançadas", self)
        # Conecta o clique do botão ao método terceiraPagina
        self.Botao_opcoes_avancadas.clicked.connect(self.terceiraPagina)
        # Adiciona o botão ao layout vertical
        self.stackedLayout.addWidget(self.Botao_opcoes_avancadas)
        # Oculta o botão inicialmente
        self.Botao_opcoes_avancadas.hide()
        
        # Botão para ativar a campainha
        self.Botao_Ativar = QPushButton("Ativar a campainha", self)
        # Conecta o clique do botão ao método Ativar
        self.Botao_Ativar.clicked.connect(self.Ativar)
        # Adiciona o botão ao layout vertical
        self.stackedLayout.addWidget(self.Botao_Ativar)
        # Oculta o botão inicialmente
        self.Botao_Ativar.hide()
        
        # Botão para desativar a campainha
        self.Botao_Desativar = QPushButton("Desativar a campainha", self)
        # Começa bloqueado
        self.Botao_Desativar.setEnabled(False) 
        # Conecta o clique do botão ao método Fechar
        self.Botao_Desativar.clicked.connect(self.Fechar)
        # Adiciona o botão ao layout vertical
        self.stackedLayout.addWidget(self.Botao_Desativar)
        # Oculta o botão inicialmente
        self.Botao_Desativar.hide()
        
        # Texto para visualizar a imagem da porta
        self.MostrarPorta = QLabel(" \u25BA Veja uma imagem da sua porta:", self)
        # Adiciona a label ao layout vertical
        self.stackedLayout.addWidget(self.MostrarPorta)
        # Oculta a label inicialmente
        self.MostrarPorta.hide()
        # Botão para abrir o link do streaming
        self.Botao_Imagem_Porta = QPushButton("abrir link", self)
        # Conecta o clique do botão ao método abrirURL
        self.Botao_Imagem_Porta.clicked.connect(self.abrirURL)
        # Adiciona o botão ao layout vertical
        self.stackedLayout.addWidget(self.Botao_Imagem_Porta)
        # Oculta o botão inicialmente
        self.Botao_Imagem_Porta.hide()
        
        # Texto da indicação de enviar uma notificação via email
        self.InstrucaoNotificacao = QLabel(" \u25BA Envie uma notificação via email:", self)
        # Adiciona a label ao layout vertical
        self.stackedLayout.addWidget(self.InstrucaoNotificacao)
        # Oculta a label inicialmente
        self.InstrucaoNotificacao.hide()
        # Botão para enviar a notificação por e-mail
        self.Botao_Notificacao = QPushButton("Enviar email", self)
        # Conecta o clique do botão ao método enviarEmail
        self.Botao_Notificacao.clicked.connect(self.enviarEmail)
        # Adiciona o botão ao layout vertical
        self.stackedLayout.addWidget(self.Botao_Notificacao)
        # Oculta o botão inicialmente
        self.Botao_Notificacao.hide()
        
        # Botão para voltar à segunda página
        self.Botao_Voltar_Pag2 = QPushButton("Voltar", self)
        # Conecta o clique do botão ao método mudarParaPag2
        self.Botao_Voltar_Pag2.clicked.connect(self.mudarParaPag2)
        # Adiciona o botão ao layout vertical
        self.stackedLayout.addWidget(self.Botao_Voltar_Pag2)
        # Oculta o botão inicialmente
        self.Botao_Voltar_Pag2.hide()
        
    def mudarParaPag2(self):
        """Muda para a segunda página da aplicação.

        Este método é chamado quando a aplicação avança para a segunda página. 
        Ele obtém o nome inserido pelo usuário, esconde os widgets da primeira página 
        e da terceira página e mostra os widgets da segunda página para permitir ao utilizador 
        selecionar a campainha, inserir uma mensagem de display e um endereço de e-mail.

        Retorna:
            None
        """
        # Obtém o nome inserido pelo usuário
        nome = self.NomeInserido.text()

        # Esconde os widgets da primeira página
        self.botao_carregar_imagem.hide()  # Esconde o botão de carregar imagem
        self.FotoSelecionada.hide()  # Esconde a label para mostrar a foto selecionada
        self.TituloPag1.hide()  # Esconde o título da primeira página
        self.NomeInserido.hide()  # Esconde o campo de inserção de nome
        self.PalavraChave.hide()  # Esconde o campo de inserção de palavra-chave
        self.Botao_Iniciar.hide()  # Esconde o botão de iniciar
        self.Botao_Voltar_Pag2.hide()  # Esconde o botão de voltar à página 2
        self.TituloPag3.hide()  # Esconde o título da terceira página
        self.Botao_Notificacao.hide()  # Esconde o botão de notificação
        self.InstrucaoNotificacao.hide()  # Esconde a instrução de notificação
        self.Botao_Imagem_Porta.hide()  # Esconde o botão de imagem da porta
        self.MostrarPorta.hide()  # Esconde a label para mostrar a porta
        self.Botao_Ativar.hide()  # Esconde o botão de ativar
        self.Botao_Desativar.hide()  # Esconde o botão de desativar

        # Mostra os widgets da segunda página
        self.TituloPag2.setText(f"Bem-vinde, {nome}")  # Define o texto do título da segunda página com o nome inserido
        self.TituloPag2.setAlignment(Qt.AlignCenter)  # Define o alinhamento do texto do título
        self.TituloPag2.show()  # Mostra o título da segunda página
        self.SelecionarSom.show()  # Mostra o texto de seleção de som
        self.CaixaComboCampainha.show()  # Mostra a caixa de combinação de campainha
        self.CampainhaSelecionada.show()  # Mostra a label para a campainha selecionada
        self.mendisplay.show()  # Mostra a label para a instrução de mensagem de display
        self.mensagemDisplay.show()  # Mostra o campo de inserção de mensagem de display
        self.emaildisplay.show()  # Mostra a label para a instrução de e-mail
        self.emailUtilizador.show()  # Mostra o campo de inserção de e-mail
        self.Botao_Voltar_Atras.show()  # Mostra o botão de voltar atrás
        self.Botao_Verificar_Campos.show()  # Mostra o botão de verificar campos
        self.Botao_mensagem.show()  # Mostra o botão de mensagem
        
        
    def mudarParaPag1(self):
        """Muda para a primeira página da aplicação.

        Este método é chamado quando a aplicação volta para a primeira página. 
        Ele oculta os widgets relacionados à segunda e terceira páginas e mostra os 
        widgets da primeira página para permitir ao usuário inserir o seu nome, carregar 
        uma foto e iniciar o processo.

        Retorna:
            None
        """
        # Oculta os widgets da segunda página
        self.TituloPag2.hide()  # Oculta o título da segunda página
        self.SelecionarSom.hide()  # Oculta o texto de seleção de som
        self.CaixaComboCampainha.hide()  # Oculta a caixa de combinação de campainha
        self.CampainhaSelecionada.hide()  # Oculta a label para a campainha selecionada
        self.Botao_Voltar_Atras.hide()  # Oculta o botão de voltar atrás
        self.mendisplay.hide()  # Oculta a label para a instrução de mensagem de display
        self.mensagemDisplay.hide()  # Oculta o campo de inserção de mensagem de display
        self.Botao_Notificacao.hide()  # Oculta o botão de notificação
        self.InstrucaoNotificacao.hide()  # Oculta a instrução de notificação
        self.emailUtilizador.hide()  # Oculta o campo de inserção de e-mail
        self.MostrarPorta.hide()  # Oculta a label para mostrar a porta
        self.emaildisplay.hide()  # Oculta a label para a instrução de e-mail
        self.emailUtilizador.hide()  # Oculta o campo de inserção de e-mail
        self.Botao_Imagem_Porta.hide()  # Oculta o botão de imagem da porta
        self.Botao_Verificar_Campos.hide()  # Oculta o botão de verificar campos
        self.Botao_Voltar_Pag2.hide()  # Oculta o botão de voltar à página 2
        self.TituloPag3.hide()  # Oculta o título da terceira página
        self.Botao_mensagem.hide()  # Oculta o botão de mensagem
        self.Botao_Ativar.hide()  # Oculta o botão de ativar
        self.Botao_Desativar.hide()  # Oculta o botão de desativar

        # Mostra os widgets da primeira página
        self.TituloPag1.show()  # Mostra o título da primeira página
        self.NomeInserido.show()  # Mostra o campo de inserção de nome
        self.botao_carregar_imagem.show()  # Mostra o botão de carregar imagem
        self.FotoSelecionada.show()  # Mostra a label para mostrar a foto selecionada
        self.Botao_Iniciar.show()  # Mostra o botão de iniciar

    def terceiraPagina(self):
        """Mostra os widgets e oculta os relacionados com a terceira página da aplicação.

        Este método é chamado quando a aplicação avança para a terceira página. Ele mostra 
        os widgets relacionados com a notificação, a imagem da porta e a ativação da campainha. 
        Além disso, ele oculta os widgets das páginas anteriores para limpar a interface gráfica.

        Retorna:
            None
        """
        # Define e mostra o título da terceira página
        self.TituloPag3.setText("Campainha inteligente: Ativação")
        self.TituloPag3.setAlignment(Qt.AlignCenter)
        self.TituloPag3.show()

        # Mostra os widgets relacionados à notificação
        self.Botao_Notificacao.show()  # Mostra o botão de notificação
        self.InstrucaoNotificacao.show()  # Mostra a instrução de notificação

        # Mostra os widgets relacionados à imagem da porta e à ativação da campainha
        self.Botao_Imagem_Porta.show()  # Mostra o botão de imagem da porta
        self.MostrarPorta.show()  # Mostra a label para mostrar a porta
        self.Botao_Ativar.show()  # Mostra o botão de ativar
        self.Botao_Desativar.show()  # Mostra o botão de desativar
        self.Botao_Voltar_Pag2.show()  # Mostra o botão de voltar à página 2

        # Esconde os widgets da primeira página
        self.TituloPag1.hide()  # Oculta o título da primeira página
        self.NomeInserido.hide()  # Oculta o campo de inserção de nome
        self.PalavraChave.hide()  # Oculta o campo de inserção de palavra-chave
        self.Botao_Iniciar.hide()  # Oculta o botão de iniciar
        self.botao_carregar_imagem.hide()  # Oculta o botão de carregar imagem
        self.FotoSelecionada.hide()  # Oculta a label para mostrar a foto selecionada

        # Esconde os widgets da segunda página
        self.TituloPag2.hide()  # Oculta o título da segunda página
        self.SelecionarSom.hide()  # Oculta o texto de seleção de som
        self.CaixaComboCampainha.hide()  # Oculta a caixa de combinação de campainha
        self.CampainhaSelecionada.hide()  # Oculta a label para a campainha selecionada
        self.mendisplay.hide()  # Oculta a label para a instrução de mensagem de display
        self.mensagemDisplay.hide()  # Oculta o campo de inserção de mensagem de display
        self.emaildisplay.hide()  # Oculta a label para a instrução de e-mail
        self.emailUtilizador.hide()  # Oculta o campo de inserção de e-mail
        self.Botao_Voltar_Atras.hide()  # Oculta o botão de voltar atrás
        self.Botao_Verificar_Campos.hide()  # Oculta o botão de verificar campos
        self.Botao_mensagem.hide()  # Oculta o botão de mensagem

    def uploadGuardarFoto(self):
        """Lida com o upload e guardar da foto do utilizador.

        Este método é chamado quando o utilizador faz o upload de uma foto. 
        Ele abre uma janela de diálogo para selecionar um arquivo de imagem, 
        carrega a imagem usando o Pillow, converte-a para o modo RGB, define o 
        caminho para guardar a imagem, guarda a imagem e atualiza o texto do QLabel para 
        indicar que a foto foi guardada com sucesso.

        Returns:
            None
        """
        # Abre uma janela de diálogo para selecionar um arquivo de imagem
        opcoes = QFileDialog.Options()
        nome_ficheiro, _ = QFileDialog.getOpenFileName(self, 'Select Photo', '', 'Image Files (*.jpg *.png)', options=opcoes)
        
        # Verifica se um arquivo foi selecionado
        if nome_ficheiro:
            # Carrega a imagem usando o Pillow
            img = Image.open(nome_ficheiro)

            # Converte para o modo RGB, se necessário
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Define o caminho para guardar a imagem
            diretorio = os.path.join(os.path.dirname(__file__), "Caras", "dono.png")

            # Guarda a imagem
            img.save(diretorio)

            # Atualiza o texto do QLabel para indicar que a foto foi guardada com sucesso
            self.FotoSelecionada.setText("Foto guardada")


    def verificarCredenciais(self):
        """Verifica as credenciais do utilizador.

        Este método é chamado quando o utilizador tenta fazer login. Ele verifica se uma 
        foto do administrador foi selecionada e se as credenciais inseridas 
        correspondem ao utilizador e senha corretos. Se as credenciais estiverem corretas, 
        muda para a segunda página; caso contrário, exibe uma mensagem de aviso.

        Returns:
            None
        """
        # Obtém o nome de usuário e senha inseridos nos campos de entrada
        usuario = self.NomeInserido.text()
        senha = self.PalavraChave.text()
        
        # Verifica se uma foto do administrador foi selecionada
        if self.FotoSelecionada.text() != "Foto guardada":
            # Exibe uma mensagem de aviso se a foto do administrador não foi selecionada
            QMessageBox.warning(self, "Foto do administrador", "Dê upload da sua foto!")
        
        # Verifica se as credenciais inseridas correspondem ao usuário e senha corretos
        elif usuario == "admin" and senha == "admin" and self.FotoSelecionada.text() == "Foto guardada":
            # Se as credenciais estiverem corretas, muda para a segunda página
            self.mudarParaPag2()
        else:
            # Se as credenciais estiverem incorretas, exibe uma mensagem de aviso
            QMessageBox.warning(self, "Login Inválido", "Usuário ou senha incorretos. Tente novamente.")


    def atualizarCampainha(self):
        """Atualiza a campainha selecionada e envia a mensagem correspondente para a campainha.

        Este método obtém o índice da campainha selecionada na CaixaComboCampainha, prepara a
        mensagem a ser enviada para a campainha selecionada, envia a mensagem através da porta
        serial e atualiza o texto para exibir a campainha selecionada.

        Retorna:
            None
        """
        # Obtém o índice da campainha selecionada na CaixaCombo
        indice_campainha = str(self.CaixaComboCampainha.currentIndex())
        
        # Imprime o índice da campainha selecionada
        print(indice_campainha)
        
        # Prepara a mensagem a ser enviada para a campainha selecionada
        mensagem_campainha = f"/{indice_campainha}"
        
        # Envia a mensagem para a campainha através da porta serial
        self.serial.write(mensagem_campainha.encode())
        
        # Atualiza o texto para exibir a campainha selecionada
        self.CampainhaSelecionada.setText(f"Campainha selecionada: {indice_campainha}")


    def mensagem(self):
        """Envia uma mensagem inserida pelo utilizador para a porta serial.

        Este método obtém o texto inserido pelo utilizador no widget mensagemDisplay e, se o texto
        não estiver vazio, o envia para a porta serial. Após o envio da mensagem, o método aguarda
        5 milissegundos.

        Retorna:
            None
        """
        # Obtém o texto inserido pelo usuário
        texto = self.mensagemDisplay.text()
        
        # Verifica se o texto não está vazio
        if texto:
            # Envia o texto para a porta serial
            self.serial.write(texto.encode())
            
            # Aguarda 5 milissegundos
            time.sleep(0.005)


    def abrirURL(self):
        """Abre a URL armazenada no atributo link no navegador padrão do sistema.

        Este método obtém a URL armazenada no atributo link da classe e a abre no navegador
        padrão do sistema utilizando o comando 'xdg-open' do sistema operacional.

        Retorna:
            None
        """
        # Obtém a URL do atributo da classe
        url = self.link
        
        # Abre a URL no navegador padrão do sistema
        os.system("xdg-open " + url)


    def enviarEmail(self):
        """Envia um email de notificação para o endereço de email fornecido pelo usuário.

        Este método utiliza a biblioteca smtplib para enviar um email de notificação para o
        endereço de email fornecido pelo usuário. O email é enviado a partir de uma conta 
        Gmail configurada com o email do remetente e a senha fornecidos no código. O assunto 
        do email é definido como 'Notificação' e o corpo da mensagem padrão é 'Olá, isto é um teste'.

        Retorna:
            None
        """
        # Configurações de email
        email_admin = "campainha.inteligente.iad@gmail.com" # Email do remetente
        password = "errn xfzo dijr lorc " # Password do email do remetente para iniciar sessão
        
        # Email do destinatário
        email_utilizador = self.emailUtilizador.text()
        
        # Criação do objeto de mensagem
        msg = MIMEMultipart()
        msg['From'] = email_admin # Define o email do remetente
        msg['To'] = email_utilizador # Define o email do destinatário
        msg['Subject'] = "Notificação" # Define o assunto do email

        session = smtplib.SMTP_SSL('smtp.gmail.com', 465) # Inicia uma sessão SMTP_SSL com o servidor do Gmail
        session.login(email_admin, password) # Faz login na conta do Gmail

        # Cria o cabeçalho da mensagem de e-mail
        msg = f'From: {email_admin}\r\nTo: {email_utilizador}\r\nContent-Type: text/plain; charset="utf-8"\r\nSubject: Notificação\r\n\r\n'
        msg += "Olá, isto é um teste"  # Adiciona o corpo da mensagem ao cabeçalho
        
        session.sendmail(email_admin, email_utilizador, msg.encode('utf8')) # Envia o e-mail
        session.quit() # Fecha a conexão com o servidor SMTP


    def verificaCamposAvancar(self):
        """Verifica se os campos estão preenchidos corretamente antes de avançar para a próxima página.

        Este método verifica se todos os campos necessários estão preenchidos corretamente antes de avançar
        para a terceira página. Os campos verificados incluem a seleção de campainha, o formato do endereço de
        email inserido e se há texto na caixa de mensagem. Se todos os campos estiverem preenchidos corretamente,
        o método avança para a terceira página. Se o endereço de email estiver em um formato inválido, exibe uma
        mensagem de aviso solicitando um endereço de email válido. Se algum campo estiver incompleto, exibe uma
        mensagem de aviso solicitando que todos os campos sejam preenchidos antes de avançar.

        Retorna:
            None
        """
        # Define o padrão para validar o formato do e-mail
        padrao = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        
        # Verifica se todos os campos estão preenchidos corretamente
        if self.CaixaComboCampainha.currentIndex() and re.match(padrao, self.emailUtilizador.text()) and self.mensagemDisplay.text():
            # Avança para a terceira página se todos os campos estiverem preenchidos corretamente
            self.terceiraPagina()
        elif not re.match(padrao, self.emailUtilizador.text()):
            # Exibe uma mensagem de aviso se o endereço de e-mail não estiver num formato válido
            QMessageBox.warning(self, "Email inválido.", "Por favor, insira um endereço de email válido.")
        else:
            # Exibe uma mensagem de aviso se algum campo estiver incompleto
            QMessageBox.warning(self, "Campos Incompletos", "Por favor, preencha todos os campos antes de avançar.")


    def Ativar(self):
        """Ativa o sistema e inicia a execução da thread Arduino.

        Este método é chamado quando o botão de ativar é pressionado. 
        Ele ativa o sistema, tornando o botão de desativar disponível para ser usado. 
        Além disso, inicializa uma instância da classe Arduino com o endereço de e-mail e a mensagem como argumentos fornecidos pelo usuário. 
        Em seguida, inicia a execução da thread Arduino para que o sistema comece a monitorar e enviar notificações conforme necessário.

        Retorna:
            None
        """
        #Ativa botão de desativar
        self.Botao_Desativar.setEnabled(True)
        # Inicializa uma instância da classe Arduino com o endereço de e-mail como argumento
        self.arduino = Arduino(self.emailUtilizador.text(), self.mensagemDisplay.text())
        # Inicia a execução da thread Arduino
        self.arduino.start()

    def Fechar(self):
        """Para a execução da thread Arduino e aguarda sua conclusão.

        Este método é chamado quando o sistema está sendo desativado. 
        Ele interrompe a execução da thread Arduino para que o sistema pare de monitorizar e 
        enviar notificações. Em seguida, aguarda até que a thread Arduino termine a sua execução 
        antes de continuar.

        Retorna:
            None
        """
        # Para a execução da thread Arduino
        self.arduino.stop()
        
        # Espera até que a thread Arduino termine a sua execução
        self.arduino.join()



# Verifica se este script é executado como programa principal
if __name__ == "__main__":
    # Cria uma instância da aplicação Qt
    app = QApplication(sys.argv)
    
    # Cria a janela principal da interface gráfica
    mainWindow = MainWindow()
    
    # Exibe a janela principal na tela
    mainWindow.show()
    
    # Inicia o loop de eventos Qt e aguarda até que a aplicação seja encerrada
    # Retorna um código de saída após encerrar a aplicação
    sys.exit(app.exec_())
