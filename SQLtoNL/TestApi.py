from flask import Flask, make_response, abort
from SQLtoNL import SQLtoNL
import MRPGraphTranslator


# Build dot code
def build_dot_code(query):
    query_string = query.get('query_string', None)
    builder = SQLtoNL(MRPGraphTranslator.MRPGraphTranslator())
    builder.translate(query_string)
    if query_string is not None:
        return {'status': True, 'message': query_string}
    else:
        return {'status': False, 'message': 'Failed to build dot code'}


# Translate query
def translate_query(query):
    query_string = query.get('query_string', None)
    translator = SQLtoNL(MRPGraphTranslator.MRPGraphTranslator())
    if query_string is not None:
        return {'status': True, 'message': translator.translate(query_string)}
    else:
        return {'status': False, 'message': 'Failed to translate query'}