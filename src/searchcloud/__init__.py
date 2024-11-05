import argparse
import re
from pathlib import Path
from typing import Any, Generator

import pyfiglet
from rich import print

from searchcloud.version import __version__

# --- Globais --- #
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
def ler_arquivos(diretorio: Path | str, extensao: str) -> list[Path]:
    """
    Ler arquivos de um diretorio e retornar uma lista de arquivos.

    Args:
        diretorio (Path | str): Caminho para o diretório.
        extensao (str): Extensão dos arquivos a serem buscados.

    Returns:
        list[Path]: Lista de arquivos encontrados.
    """
    if not isinstance(diretorio, Path):
        diretorio = Path(diretorio)

    print(f"Buscando por arquivos com extensão .{extensao} no diretório: {diretorio}")

    tmp = [arq if arq.is_file() else None for arq in diretorio.glob(f"**/*.{extensao}")]
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
        print(f"Lendo arquivo: {arquivo}")
        for linha in arquivo.read_text().splitlines():
            if VERBOSO:
                print(f"Leitura da linha: {linha}")
            yield linha
    except Exception as e:
        print(f"Erro lendo o arquivo: {e}")
        yield None


def buscar_termo(linha: str, termo: str) -> str | None:
    """
    Buscar um termo em uma linha.

    Args:
        linha (str): Linha a ser pesquisada.
        termo (str): Termo a ser pesquisado.

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
        help="Termo de busca",
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
        "-v",
        "--verboso",
        action="store_true",
        help="Modo de verbosidade",
    )
    args = parser.parse_args()

    # Definir modo de verbosidade
    global VERBOSO
    VERBOSO = args.verboso

    # Buscando arquivos
    diretorio_operacao = DIRETORIO_CHAMADO if args.diretorio == "." else args.diretorio
    arquivos = ler_arquivos(diretorio_operacao, extensao=args.extensao)
    if len(arquivos) == 0:
        return None

    # Buscando termo
    LINHAS = []
    for arquivo in arquivos:
        for linha in ler_arquivo(arquivo):
            if linha is None:
                continue
            elif linha_valida := buscar_termo(linha, termo=args.termo):
                LINHAS.append(linha_valida)

    # Devolver resultados
    if args.salvar:
        with open(args.salvar, "w") as arquivo:
            arquivo.write("\n".join(LINHAS))
        print(f"Resultados salvo em: {args.salvar}")
    else:
        print(f"Total de linhas encontradas: {len(LINHAS)}")
        if len(LINHAS) > 0:
            print("Linhas encontradas:")
            print("\n".join(LINHAS))
