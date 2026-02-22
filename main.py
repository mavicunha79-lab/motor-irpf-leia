from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Modelo de dados que a Léia vai enviar
class DadosIRRF(BaseModel):
    rendimento_bruto: float
    deducoes_legais: float = 0.0

def arredondar(valor: float) -> float:
    # Regra de arredondamento: fixar em 2 casas decimais [cite: 39, 101]
    return round(valor, 2)

def calcular_ir_tabela(base_calculo: float) -> float:
    # Tabela Progressiva Mensal [cite: 198-203]
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
    
    # Cálculo: (BC * Alíquota) - Parcela a deduzir [cite: 94]
    ir_t = (base_calculo * aliquota) - parcela_deduzir
    return arredondar(ir_t)

@app.post("/calcular")
def engine_irrf(dados: DadosIRRF):
    R = dados.rendimento_bruto
    DL = dados.deducoes_legais
    DS = 607.20  # Desconto Simplificado fixo [cite: 122]

    # Escolhe a maior dedução [cite: 91]
    D = max(DL, DS)

    # Base de Cálculo [cite: 92]
    BC = arredondar(R - D)

    # Imposto pela Tabela Progressiva [cite: 93]
    ir_t = calcular_ir_tabela(BC)

    # Cálculo da Redução Lei nº 15.270/2025 [cite: 15-36]
    if R <= 5000.00:
        reducao = ir_t
    elif R <= 7350.00:
        # Redução = 978,62 - (0,133145 * R) [cite: 23]
        A = arredondar(0.133145 * R)
        reducao = arredondar(978.62 - A)
    else:
        reducao = 0.0

    # Limites de segurança da redução [cite: 44-50]
    reducao = max(0.0, min(reducao, ir_t))

    # Resultado Final [cite: 97]
    irrf_final = arredondar(ir_t - reducao)

    return {
        "irrf_final": max(0.0, irrf_final),
        "detalhes": {
            "rendimento": R,
            "base_calculo": BC,
            "deducao_utilizada": "Simplificada" if D == DS else "Legais",
            "imposto_tabela": ir_t,
            "reducao_aplicada": reducao
        }
    }
