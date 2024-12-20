import argparse
import re
import time
from pathlib import Path
from typing import Any, Generator

import pyfiglet
from rich import print

from searchcloud.version import __version__

# --- Globais --- #
BUFFER = False
VERBOSO = False
DIRETORIO_BASE = Path(__file__).parent
DIRETORIO_CHAMADO = Path.cwd()


# --- Tipos --- #
def tipo_extensao(valor: str) -> str:
    """
    Verificar se o valor é uma extensão válida.

    Args:
        valor (str): Valor a ser verificado.

    Returns:
        str: Extensão válida.
    """
    return valor.removeprefix(".")


# --- Funções auxiliares --- #
def formatar_duracao(segundos: float) -> str:
    """
    Formatar a duração em horas, minutos e segundos.

    Args:
        segundos (float): Duração em segundos.

    Returns:
        str: Duração formatada em horas, minutos e segundos.
    """
    horas, remainder = divmod(int(segundos), 3600)
    minutos, segundos = divmod(remainder, 60)
    return f"{horas:02}:{minutos:02}:{segundos:02}"


def ler_arquivos(diretorio: Path | str, extensao: str) -> list[Path]:
    """
    Ler arquivos de um diretorio e retornar uma lista de arquivos.

    Args:
        diretorio (Path | str): Diretório de busca ou arquivo.
        extensao (str): Extensão dos arquivos a serem buscados.

    Returns:
        list[Path]: Lista de arquivos encontrados.
    """
    if not isinstance(diretorio, Path):
        diretorio = Path(diretorio)

    if diretorio.is_file():
        arquivos = [diretorio]
    else:
        print(
            f"Buscando por arquivos com extensão .{extensao} no diretório: {diretorio}"
        )
        tmp = [
            arq if arq.is_file() else None for arq in diretorio.glob(f"**/*.{extensao}")
        ]
        arquivos = list(filter(None, tmp))

    print(f"Total de arquivos encontrados: {len(arquivos)}")
    if VERBOSO:
        print("Lista de arquivos encontrados:")
        for arq in arquivos:
            print(arq)

    return arquivos


def ler_arquivo(arquivo: Path) -> Generator[str, Any, None]:
    """
    Ler um arquivo e retornar uma linha de cada vez.

    Args:
        arquivo (Path): Caminho para o arquivo.

    Yields:
        str | None: Linha do arquivo.
    """
    try:
        if VERBOSO:
            print(f"Lendo arquivo: {arquivo}")

        # Carrega o arquivo em memória
        if BUFFER:
            for linha in arquivo.read_text(encoding="utf-8").splitlines():
                if VERBOSO:
                    print(f"Leitura da linha: {linha}")
                yield linha
        # Carrega o arquivo linha por linha
        else:
            with arquivo.open("r", encoding="utf-8") as f:
                for linha in f:
                    linha = linha.strip()  # Remover espaços e quebras de linha extras
                    if VERBOSO:
                        print(f"Leitura da linha: {linha}")
                    yield linha
    except Exception as e:
        if VERBOSO:
            print(f"Erro lendo o arquivo: {e}")
        yield None


def buscar_termo(linha: str, termo: re.Pattern) -> str | None:
    """
    Buscar um termo em uma linha.

    Args:
        linha (str): Linha a ser pesquisada.
        termo (re.Pattern): Termo a ser pesquisado.

    Returns:
        str | None: Linha encontrada.
    """
    if re.search(termo, string=linha):
        if VERBOSO:
            print(f"Encontrado na linha: {linha}")
        return linha
    else:
        return None


# --- Main --- #
def main() -> None:
    start_time = time.time()

    # Apresentação
    ascii_art = pyfiglet.figlet_format("SearchCloud")
    print(ascii_art)

    # Argumentos
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-V", "--versao", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument(
        "termo",
        type=str,
        help="Termo de busca (texto literal ou expressão regular)",
    )
    parser.add_argument(
        "-r",
        "--regex",
        action="store_true",
        help="Usar expressão regular (padrão: False)",
    )
    parser.add_argument(
        "-i",
        "--ignorecase",
        action="store_true",
        help="Ignorar maiúsculas e minúsculas (padrão: False)",
    )
    parser.add_argument(
        "-d",
        "--diretorio",
        default=".",
        type=str,
        help="Diretorio de busca (padrão: .)",
    )
    parser.add_argument(
        "-e",
        "--extensao",
        default="txt",
        type=tipo_extensao,
        help="Extensão dos arquivos a serem buscados (padrão: txt)",
    )
    parser.add_argument(
        "-s",
        "--salvar",
        type=str,
        help="Salvar resultados em um arquivo",
    )
    parser.add_argument(
        "-b",
        "--buffer",
        action="store_true",
        help="Usar buffer (carregar em memória todos os arquivos. padrão: False)",
    )
    parser.add_argument(
        "-v",
        "--verboso",
        action="store_true",
        help="Modo de verbosidade (deixa a execução mais lenta)",
    )
    args = parser.parse_args()

    # Definir modo de buffer
    global BUFFER
    BUFFER = args.buffer

    # Definir modo de verbosidade
    global VERBOSO
    VERBOSO = args.verboso

    # Buscando arquivos
    diretorio_operacao = DIRETORIO_CHAMADO if args.diretorio == "." else args.diretorio
    arquivos = ler_arquivos(diretorio_operacao, extensao=args.extensao)
    if len(arquivos) == 0:
        return None

    # Buscando termo
    _flags = re.IGNORECASE if args.ignorecase else 0
    _termo = (
        re.compile(re.escape(args.termo), flags=_flags)
        if not args.regex
        else re.compile(args.termo, flags=_flags)
    )

    # Devolver resultados
    total_resultados = 0
    if args.salvar:
        # Gravando tudo na memória
        if BUFFER:
            LINHAS = []
            for arquivo in arquivos:
                for linha in ler_arquivo(arquivo):
                    if linha is None:
                        continue
                    elif linha_valida := buscar_termo(linha, termo=_termo):
                        LINHAS.append(linha_valida)
            total_resultados = len(LINHAS)
        # Gravando com buffer automatico
        else:
            with open(args.salvar, "w") as arquivo:
                for arquivo_analise in arquivos:
                    for linha in ler_arquivo(arquivo_analise):
                        if linha is None:
                            continue
                        elif linha_valida := buscar_termo(linha, termo=_termo):
                            total_resultados += 1
                            arquivo.write(linha_valida + "\n")
        print(f"Resultados salvo em: {args.salvar}")
    else:
        for arquivo in arquivos:
            for linha in ler_arquivo(arquivo):
                if linha is None:
                    continue
                elif buscar_termo(linha, termo=_termo):
                    total_resultados += 1
        print("Use -s para salvar os resultados")
    print(f"Total de linhas encontradas: {total_resultados}")

    # Mostrar tempo de execução
    end_time = time.time()
    print(f"Tempo de execução: {formatar_duracao(end_time - start_time)}")
