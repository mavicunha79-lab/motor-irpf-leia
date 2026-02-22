from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# Ajustado para aceitar qualquer um dos nomes que a Léia enviar
class DadosIRRF(BaseModel):
    rendimento: Optional[float] = None
    rendimento_bruto: Optional[float] = None
    deducoes_legais: float = 0.0

def arredondar(valor: float) -> float:
    """Regra de arredondamento oficial da Contabilidade Real."""
    return round(valor, 2)

def calcular_ir_tabela(base_calculo: float) -> float:
    """Tabela Progressiva Mensal - Lei 15.270/2025."""
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

@app.post("/calcular")
def engine_irrf(dados: DadosIRRF):
    # Aqui está a correção do Item 4:
    # Ele verifica qual nome a Léia usou e guarda o valor na letra R
    R = dados.rendimento if dados.rendimento is not None else dados.rendimento_bruto
    
    if R is None:
        return {"error": "Rendimento não informado ou nome do campo inválido"}

    DL = dados.deducoes_legais
    DS = 607.20  # Desconto Simplificado fixo

    # 1. Escolha da Dedução
    D = max(DL, DS)

    # 2. Base de Cálculo (BC)
    BC = arredondar(R - D)

    # 3. Imposto pela Tabela (IRt)
    ir_t = calcular_ir_tabela(BC)

    # 4. Redução Lei nº 15.270/2025
    if R <= 5000.00:
        reducao = ir_t
    elif R <= 7350.00:
        A = arredondar(0.133145 * R)
        reducao = arredondar(978.62 - A)
    else:
        reducao = 0.0

    # 5. Travas de Segurança
    reducao = max(0.0, min(reducao, ir_t))

    # 6. IRRF Final
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
