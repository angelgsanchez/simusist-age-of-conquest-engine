import random

# ==========================================
# FUNCIONES AUXILIARES MATEMÁTICAS
# ==========================================
def Sat(x):
    """Función de saturación para mantener variables en el espacio topológico [0, 100]."""
    return max(0.0, min(100.0, x))

# ==========================================
# CLASES DE ESTADO (STOCKS)
# ==========================================
class Provincia:
    def __init__(self, nombre, propietario, poblacion, tropas, felicidad=100.0):
        self.nombre = nombre
        self.propietario = propietario
        self.poblacion = poblacion
        self.tropas = tropas
        self.felicidad = felicidad # Hit: Nivel de Felicidad [0, 100]

class Imperio:
    def __init__(self, nombre, oro_inicial, tasa_impuestos):
        self.nombre = nombre
        self.oro = oro_inicial
        self.tasa_impuestos = tasa_impuestos
        self.es_protectorado = False # esProtectorado: Estado del Régimen Político

# ==========================================
# MOTOR DE SIMULACIÓN
# ==========================================
class MotorAgeOfConquest:
    def __init__(self):
        self.turnos_transcurridos = 0
        self.imperios = {}
        self.mapa = {}
        
        # Matriz de Parámetros Fijos (Constantes del Juego)
        self.delta = 8.0        # Coeficiente de Shock Bélico (Moral)
        self.delta_Hrey = 20.0  # Penalización por Anarquía Institucional
        self.p_muerte = 0.25    # Probabilidad de Muerte del Líder

    def registrar_imperio(self, imperio):
        self.imperios[imperio.nombre] = imperio

    def registrar_provincia(self, provincia):
        self.mapa[provincia.nombre] = provincia

    def resolver_conflicto(self, prov_origen, prov_destino, tropas_atacantes, rey_presente=False, mu_terreno=1.0):
        """
        Subsistema Militar: Modelo de Resolución de Combate basado en 
        las Ecuaciones de Combate de Lanchester adaptadas a tiempo discreto.
        """
        origen = self.mapa[prov_origen]
        destino = self.mapa[prov_destino]
        imperio_atacante = self.imperios[origen.propietario]
        
        if origen.tropas < tropas_atacantes:
            print("[ERROR LOGÍSTICO] Tropas insuficientes para iniciar campaña.")
            return

        print(f"\n[COMBATE] {origen.propietario} ataca {destino.nombre} ({destino.propietario}) con {tropas_atacantes} soldados.")
        origen.tropas -= tropas_atacantes
        
        # Inicialización de las iteraciones de asalto (k)
        A_k = float(tropas_atacantes) # Tropas del ejército Atacante
        D_k = float(destino.tropas)   # Tropas del ejército Defensor
        
        # Multiplicadores
        mu_rey = 1.25 if rey_presente else 1.00 # Multiplicador de daño por presencia del líder
        eficacia_A = 0.10 # Constante base de letalidad ofensiva
        eficacia_D = 0.10 # Constante base de letalidad defensiva
        
        k = 0 # Iterador del bucle de asaltos
        
        # Condiciones de Parada: El bucle finaliza cuando A_k+1 = 0 o D_k+1 = 0
        while A_k > 0 and D_k > 0:
            k += 1
            
            # Inyección de variables aleatorias independientes (Uniforme Continua)
            # Modela factores climáticos o estratégicos no visibles oscilando entre 70% y 130%
            X_A = random.uniform(0.7, 1.3)
            X_D = random.uniform(0.7, 1.3)
            
            # Ecuaciones de Transición Táctica (Bajas por Asalto)
            delta_A_k = D_k * eficacia_D * X_D
            delta_D_k = A_k * eficacia_A * mu_rey * mu_terreno * X_A
            
            # Actualización de estados asegurando el límite inferior en 0
            A_k = max(0.0, A_k - delta_A_k)
            D_k = max(0.0, D_k - delta_D_k)
            
        A_k = int(A_k)
        D_k = int(D_k)
        
        # ==========================================
        # RESOLUCIÓN E IMPACTO EN LAS VARIABLES DE ESTADO
        # ==========================================
        if A_k > 0:
            print(f"[VICTORIA TÁCTICA] ¡{origen.propietario} conquista {destino.nombre} en {k} iteraciones! Sobreviven {A_k} tropas.")
            destino.propietario = origen.propietario
            destino.tropas = A_k
        else:
            print(f"[DERROTA TÁCTICA] {destino.propietario} retiene el territorio tras {k} iteraciones. Sobreviven {D_k} tropas.")
            destino.tropas = D_k
            
            # Castigo directo sobre la felicidad del territorio de origen por derrota militar
            origen.felicidad = Sat(origen.felicidad - self.delta)
            print(f"[SHOCK BÉLICO] La felicidad en {origen.nombre} cae a {origen.felicidad:.1f}%.")
            
            # Evaluación del Evento Estocástico Crítico (Muerte del Rey)
            if rey_presente:
                print(f"[*] El Rey estaba en la batalla. Calculando supervivencia...")
                # Distribución de Bernoulli para la muerte del comandante tras perder
                Z = 1 if random.random() <= self.p_muerte else 0 
                
                if Z == 1:
                    print(f"[CRÍTICO] ¡El Rey de {origen.propietario} ha sido ejecutado en el campo de batalla!")
                    # Modificación inmediata de la variable booleana global
                    imperio_atacante.es_protectorado = True 
                    # Contracción matemática sobre la felicidad por anarquía institucional
                    origen.felicidad = Sat(origen.felicidad - self.delta_Hrey) 
                    print(f"[ANARQUÍA] {origen.propietario} pierde su soberanía (esProtectorado=True). La moral local se desploma a {origen.felicidad:.1f}%.")
                else:
                    print("[*] El Rey logró escapar con vida.")

# ==========================================
# ÁREA DE PRUEBAS Y SIMULACIÓN
# ==========================================
if __name__ == "__main__":
    motor = MotorAgeOfConquest()
    
    # 1. Configuración de Estados Iniciales
    motor.registrar_imperio(Imperio("Imperio Romano", oro_inicial=500, tasa_impuestos=1.0))
    motor.registrar_imperio(Imperio("Tribus Galas", oro_inicial=200, tasa_impuestos=0.8))
    
    motor.registrar_provincia(Provincia("Roma Central", "Imperio Romano", poblacion=10000, tropas=200, felicidad=80.0))
    motor.registrar_provincia(Provincia("Galia del Sur", "Tribus Galas", poblacion=5000, tropas=150, felicidad=75.0))
    
    # 2. Simular un combate con el Rey atacando (para forzar la evaluación estocástica)
    # Probaremos enviar menos tropas para que el atacante pierda y veamos el comportamiento límite.
    motor.resolver_conflicto("Roma Central", "Galia del Sur", tropas_atacantes=100, rey_presente=True, mu_terreno=1.1)
