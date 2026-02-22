from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Esta parte foi blindada para aceitar qualquer nome de campo
class DadosIRRF(BaseModel):
    rendimento: Optional[float] = None
    rendimento_bruto: Optional[float] = None
    valor: Optional[float] = None
    deducoes_legais: float = 0.0

def arredondar(valor: float) -> float:
    return round(valor, 2)

def calcular_ir_tabela(base_calculo: float) -> float:
    if base_calculo <= 2428.80:
        aliquota, parcela_deduzir = 0.0, 0.0
    elif base_calculo <= 2826.65:
        aliquota, parcela_deduzir = 0.075, 182.16
    elif base_calculo <= 3751.05:
        aliquota, parcela_deduzir = 0.15, 394.16
    elif base_calculo <= 4664.68:
        aliquota, parcela_deduzir = 0.225, 675.49
    else:
        aliquota, parcela_deduzir = 0.275, 908.73
    
    ir_t = (base_calculo * aliquota) - parcela_deduzir
    return arredondar(ir_t)

@app.get("/")
def home():
    return {"status": "Motor da Leia Online", "versao": "1.1"}

@app.post("/calcular")
def engine_irrf(dados: DadosIRRF):
    # Procura o valor em qualquer um dos campos possíveis
    R = dados.rendimento or dados.rendimento_bruto or dados.valor
    
    if R is None:
        return {"error": "Por favor, informe o valor do rendimento."}

    DL = dados.deducoes_legais
    DS = 607.20 
    D = max(DL, DS)
    BC = arredondar(R - D)
    ir_t = calcular_ir_tabela(BC)

    # Redução Lei nº 15.270/2025
    if R <= 5000.00:
        reducao = ir_t
    elif R <= 7350.00:
        A = arredondar(0.133145 * R)
        reducao = arredondar(978.62 - A)
    else:
        reducao = 0.0

    reducao = max(0.0, min(reducao, ir_t))
    irrf_final = arredondar(ir_t - reducao)

    return {
        "irrf_final": max(0.0, irrf_final),
        "detalhes": {
            "rendimento_bruto": R,
            "base_calculo": BC,
            "deducao_utilizada": "Simplificada" if D == DS else "Legais",
            "imposto_tabela": ir_t,
            "reducao_aplicada": reducao
        }
    }