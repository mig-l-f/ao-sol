# Ao-Sol: projectos solares de auto-consumo

## Descrição

Projecto é composto por uma biblioteca em python e jupyter notebooks com exemplos de utilização para análise de UPAC com e sem armazenamento.

Biblioteca com várias funções para:
- ler dados de consumo: perfis de consumo e-redes e dados medidos e-redes
- obter dados de produção para um local através da API do PVGIS
- analisar as series temporais horárias do sistema e estimar vários indicadores de performance: auto-suficiência (IAS), auto-consumo (IAC), entrega à rede (IER), número de horas equivalentes.
- analise da performance da bateria: numero de ciclos, tempo à capacidade máxima e mínima.
- analise financeira do projecto para o tempo de vida: VAL, TIR, tempo de retorno, LCOE.

## Fontes:

<a id="1">[1]</a> 
João Carvalho. 2018
Análise da viabilidade económica do armazenamento de energia em autoprodução.
Tese de mestrado. FEUP

<a id="2">[2]</a> 
Bloco 9 - Análise Investimentos, Universidade Evora.
Em https://dspace.uevora.pt/rdpc/bitstream/10174/6309/11/BLOCO9.pdf

<a id="3">[3]</a> 
F Militão, J Alberto. 2012 
"O Método de Newton-Raphson no Cálculo do TIR", 
UNOPAR Cient. Exatas Tecnol., Londrina, v. 11, n. 1, p. 59-63

<a id="4">[4]</a> 
SJ Andrews, B Smith, MG Deceglie, KA Horowitz, and TJ Silverman. 2021
“NREL Comparative PV LCOE Calculator.” 
Version 2.0.0

