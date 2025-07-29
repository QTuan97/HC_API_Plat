from pybars import Compiler

compiler = Compiler()

def render_handlebars(template_str: str, context: dict) -> str:
    tmpl = compiler.compile(template_str)
    result = tmpl(context)
    return result.decode() if isinstance(result, (bytes, bytearray)) else result