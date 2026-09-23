"""Camada de análise de dados do SonarGest.

Separada da aplicação de propósito: a aplicação registra o dado (OLTP) e
esta camada lê o mesmo banco para responder perguntas de negócio (OLAP).
O dashboard e o notebook consomem estas funções — nenhum cálculo é
duplicado nas telas.
"""
