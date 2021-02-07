# from flask import Flask, make_response, abort
# from flask_restful import Api, reqparse, Resource

import connexion

app = connexion.App(__name__, specification_dir='./config')

# Read the swagger.yml file to configure the endpoints
app.add_api('swagger.yml')


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int("8080"), debug=True)