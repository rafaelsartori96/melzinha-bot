# Letícia Mayumi A. Tateishi
# Rafael Sartori M. Santos

# encoding: utf-8

import json
import glob
import random
import logging

from telegram import Bot
from telegram.ext import Updater
from telegram.ext import CommandHandler, MessageHandler, Filters

from datetime import time


CAMINHO_CONFIGURACAO = 'config.json'


def get_config():
    # Abrimos o arquivo de configuração como leitura
    with open(CAMINHO_CONFIGURACAO, mode='rt', encoding='utf-8') as arquivo:
        # Carregamos o JSON a partir do arquivo
        return json.load(arquivo)


def salvar_config(configuracao):
    # Abrimos o arquivo de configuração com escrita
    with open(CAMINHO_CONFIGURACAO, mode='wt', encoding='utf-8') as arquivo:
        # Salvamos o arquivo de configuração JSON
        json.dump(configuracao, arquivo, indent='\t')


def get_lista_cached_fotos(configuracao=get_config()):
    # Pegamos os caminhos das fotos
    arquivos_fotos = glob.glob(configuracao['caminho_fotos'] + '*.jpg', recursive=True)
    # Pegamos as fotos em cache
    fotos_cache = configuracao['fotos_cadastradas']
    # Procuramos por fotos recém colocadas no bot
    for arquivo in arquivos_fotos:
        # Se não está no dicionário de cache, colocamos sem cache
        if arquivo not in fotos_cache:
            fotos_cache[arquivo] = None
    # Retornamos a lista de pares (caminho, cache id)
    return list(fotos_cache.items())


def get_foto_aleatoria(fotos=get_lista_cached_fotos()):
    # Pegamos um par aleatório (caminho, cache)
    return random.choice(fotos)


def enviar_foto_com_cache(bot, chat_id, fotos=get_lista_cached_fotos()):
    # Pegamos uma foto aleatória
    caminho, cache = get_foto_aleatoria(fotos)
    # Determinamos se há cache ou não
    if cache is not None:
        bot.send_photo(chat_id, cache)
    else:
        # Abrimos o caminho da foto
        with open(caminho, 'rb') as foto:
            # Enviamos a mensagem
            mensagem = bot.send_photo(chat_id, foto)
        # Na mensagem enviada, procuramos o id da foto para colocar em cache
        if (mensagem is not None and mensagem.photo is not None):
            # Determinamos o maior tamanho da foto retornado pela mensagem
            maior_foto = None
            maior_tamanho = None
            for foto in mensagem.photo:
                dimensao = foto.width**2 + foto.height**2
                # Substituimos a maior foto salva que encontrarmos
                if (maior_foto is None or dimensao >= maior_tamanho):
                    maior_foto = foto.file_id
                    maior_tamanho = dimensao
            # Se saímos do laço com uma foto existente, colocamos na configuração
            if maior_foto is not None:
                # Adicionamos a foto ao dicionário e salvamos
                configuracao = get_config()
                configuracao['fotos_cadastradas'][caminho] = maior_foto
                salvar_config(configuracao)



def cmd_help(update, context):
    # Enviamos uma mensagem explicando o bot
    update.message.reply_text(
        """A melzinha pode te enviar uma foto diariamente se você se inscrever.

        Pode utilizar /inscrever para isso e
        /cancelar_inscricao para infelizmente parar de receber as fotos.

        Se quiser, ainda tem /mel para receber uma foto da Mel sem compromisso."""
    )


def cmd_mel(update, context):
    # Conferimos se estamos num chat válido (possui chat id)
    if update.effective_chat is not None:
        # Enviamos uma foto aleatória
        enviar_foto_com_cache(context.bot, update.effective_chat.id)


def cmd_inscrever(update, context):
    # Conferimos se temos chat id
    if update.effective_chat is None:
        return

    # Pegamos o chat id do chat
    chat_id = update.effective_chat.id
    # Pegamos a configuração
    configuracao = get_config()

    # Conferimos se já é inscrito
    if chat_id in configuracao['inscritas']:
        update.message.reply_text('Essa conversa já está inscrita e deve receber uma linda foto da Mel todo dia <3')
        return

    # Se não é, inscrevemos o ID e salvamos o JSON
    configuracao['inscritas'].append(chat_id)
    salvar_config(configuracao)
    update.message.reply_text('Inscrição feita. Essa conversa deve receber uma foto da Mel todo dia!! Parabéns!!!')


def cmd_cancelar_inscricao(update, context):
    # Conferimos se temos chat id
    if update.effective_chat is None:
        return

    # Pegamos o chat id do chat
    chat_id = update.effective_chat.id
    # Pegamos a configuração
    configuracao = get_config()

    # Conferimos se o chat não está inscrito
    if chat_id not in configuracao['inscritas']:
        update.message.reply_text('Você precisa se inscrever primeiro!! Veja mais a Melzinha!')
        return

    # Se usuário foi inscrito, removemos e salvamos o JSON
    configuracao['inscritas'].remove(chat_id)
    salvar_configuracao(configuracao)
    update.message.reply_text('Inscrição cancelada. Mas a Mel ainda te ama')


def processar_inscricoes(context):
    configuracao = get_config()
    print('Enviando mensagem às', len(configuracao['inscritas']), 'conversas inscritas.')
    # Pegamos a lista de fotos (para agilizar o envio)
    fotos = get_lista_cached_fotos(configuracao)
    # Para cada chat...
    for inscrito in configuracao['inscritas']:
        # ... enviamos uma foto aleatória
        enviar_foto_com_cache(context.bot, inscrito, fotos)



# Na thread inicial, configuramos e aguardamos as respostas do bot
if __name__ == "__main__":
    # Ativamos logging do bot
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # Iniciamos updater
    updater = Updater(get_config()['token'], use_context=True)

    # Definimos horário e mostramos imagem diariamente
    horario = time(12, 0, 0)
    job_daily = updater.job_queue.run_daily(processar_inscricoes, horario)

    # Adicionamos handler para comandos
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", cmd_help))
    dispatcher.add_handler(CommandHandler("help", cmd_help))
    dispatcher.add_handler(CommandHandler("mel", cmd_mel))
    dispatcher.add_handler(CommandHandler("inscrever", cmd_inscrever))
    dispatcher.add_handler(CommandHandler("cancelar_inscricao", cmd_cancelar_inscricao))

    # Iniciamos o bot
    updater.start_polling()

    # Idle até Ctrl+C
    updater.idle()
