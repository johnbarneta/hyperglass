"""
Renders Jinja2 & Sass templates for use by the front end application
"""
# Standard Library Imports
import json
import subprocess
from pathlib import Path

# Third Party Imports
import jinja2
from logzero import logger

# Project Imports
from hyperglass.configuration import logzero_config  # noqa: F401
from hyperglass.configuration import params
from hyperglass.exceptions import HyperglassError

# Module Directories
working_directory = Path(__file__).resolve().parent
hyperglass_root = working_directory.parent
file_loader = jinja2.FileSystemLoader(str(working_directory))
env = jinja2.Environment(
    loader=file_loader, autoescape=True, extensions=["jinja2.ext.autoescape"]
)


def render_frontend_config():
    """
    Renders user config to JSON file so front end config can be used by
    Javascript
    """
    rendered_frontend_file = hyperglass_root.joinpath("static/frontend.json")
    try:
        with rendered_frontend_file.open(mode="w") as frontend_file:
            frontend_file.write(params.json())
    except jinja2.exceptions as frontend_error:
        logger.error(f"Error rendering front end config: {frontend_error}")
        raise HyperglassError(frontend_error)


def get_fonts():
    """Downloads google fonts"""
    font_dir = hyperglass_root.joinpath("static/fonts")
    font_bin = str(
        hyperglass_root.joinpath("static/node_modules/get-google-fonts/cli.js")
    )
    font_base = "https://fonts.googleapis.com/css?family={p}|{m}&display=swap"
    font_primary = "+".join(params.branding.font.primary.split(" ")).strip()
    font_mono = "+".join(params.branding.font.mono.split(" ")).strip()
    font_url = font_base.format(p=font_primary + ":300,400,700", m=font_mono + ":400")
    proc = subprocess.Popen(
        ["node", font_bin, "-w", "-i", font_url, "-o", font_dir],
        cwd=hyperglass_root.joinpath("static"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout, stderr = proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        output_error = stderr.decode("utf-8")
        logger.error(output_error)
        raise HyperglassError(f"Error downloading font from URL {font_url}")
    else:
        proc.kill()
        logger.debug(f"Downloaded font from URL {font_url}")


def render_theme():
    """Renders Jinja2 template to Sass file"""
    rendered_theme_file = hyperglass_root.joinpath("static/theme.sass")
    try:
        template = env.get_template("templates/theme.sass.j2")
        rendered_theme = template.render(params.branding)
        with rendered_theme_file.open(mode="w") as theme_file:
            theme_file.write(rendered_theme)
    except jinja2.exceptions as theme_error:
        logger.error(f"Error rendering theme: {theme_error}")
        raise HyperglassError(theme_error)


def build_assets():
    """Builds, bundles, and minifies Sass/CSS/JS web assets"""
    proc = subprocess.Popen(
        ["yarn", "--silent", "--emoji", "false", "--json", "--no-progress", "build"],
        cwd=hyperglass_root.joinpath("static"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout, stderr = proc.communicate(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
    output_out = json.loads(stdout.decode("utf-8").split("\n")[0])
    if proc.returncode != 0:
        output_error = json.loads(stderr.decode("utf-8").strip("\n"))
        logger.error(output_error["data"])
        raise HyperglassError(
            f'Error building web assets with script {output_out["data"]}:'
            f'{output_error["data"]}'
        )
    logger.debug(f'Built web assets with script {output_out["data"]}')


def render_assets():
    """
    Controller function for rendering sass theme elements and building
    web assets
    """
    try:
        logger.debug("Rendering front end config...")
        render_frontend_config()
        logger.debug("Rendered front end config")
    except HyperglassError as frontend_error:
        raise HyperglassError(frontend_error)
    try:
        logger.debug("Downloading theme fonts...")
        get_fonts()
        logger.debug("Downloaded theme fonts")
    except HyperglassError as theme_error:
        raise HyperglassError(theme_error)
    try:
        logger.debug("Rendering theme elements...")
        render_theme()
        logger.debug("Rendered theme elements")
    except HyperglassError as theme_error:
        raise HyperglassError(theme_error)
    try:
        logger.debug("Building web assets...")
        build_assets()
        logger.debug("Built web assets")
    except HyperglassError as assets_error:
        raise HyperglassError(assets_error)
