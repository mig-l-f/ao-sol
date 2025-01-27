% ao-sol documentation master file, created by
% sphinx-quickstart on Tue Nov 12 22:02:07 2024.
% You can adapt this file completely to your liking, but it should at least
% contain the root `toctree` directive.

# Ao-Sol: projectos solares de auto-consumo

## Descrição

Projecto é composto por uma biblioteca em python e jupyter notebooks com exemplos de utilização para análise de UPAC com e sem armazenamento.

Biblioteca com várias funções para:
- ler dados de consumo: perfis de consumo e-redes e dados medidos e-redes
- obter dados de produção para um local através da API do PVGIS
- analisar as series temporais horárias do sistema e estimar vários indicadores de performance: auto-suficiência (IAS), auto-consumo (IAC), entrega à rede (IER), número de horas equivalentes.
- analise da performance da bateria: numero de ciclos, tempo à capacidade máxima e mínima.
- analise financeira do projecto para o tempo de vida: VAL, TIR, tempo de retorno, LCOE.

## Como começar:

Ver documentação de como instalar em {ref}`Instalação`

Ver os exemplos jupyter notebook em {ref}`Exemplos`

## Atribuição

Calculo dos fluxos de energia e estudos paramétricos derivados de Quoilin _et al._ [1], código original disponivel [aqui](https://github.com/squoilin/Self-Consumption) e [aqui](https://github.com/energy-modelling-toolkit/prosumpy)

Funções para obter dados do PVGIS derivados do PVLIB [5], biblioteca original disponivel [aqui](https://github.com/pvlib/pvlib-python)

## Fontes:

<a id="1">[1]</a> 
S. Quoilin, K. Kavvadias, A. Mercier, I. Pappone, A. Zucker, 
Quantifying self-consumption linked to solar home battery systems: statistical analysis and economic assessment, 
Applied Energy, 2016
Em https://doi.org/10.1016/j.apenergy.2016.08.077

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

<a id="5">[5]</a>
Jensen, A., Anderson, K., Holmgren, W., Mikofski, M., Hansen, C., Boeman, L., Loonen, R. “pvlib iotools — Open-source Python functions for seamless access to solar irradiance data.” Solar Energy, 266, 112092, (2023). DOI: 10.1016/j.solener.2023.112092.

<a id="6">[6]</a>
Naldi, Claudia & Morini, Gian & Zanchini, E.. (2014). A method for the choice of the optimal balance-point temperature of air-to-water heat pumps for heating. Sustainable Cities and Society. Em https://doi.org/10.1016/j.scs.2014.02.005

```{toctree}
:caption: 'Contents:'
:maxdepth: 2

instalacao/Instalacao
exemplos/index
```