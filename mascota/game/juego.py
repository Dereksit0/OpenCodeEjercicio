"""Reglas de la partida: turnos, eventos, derrota y reinicio.

Este modulo NO importa Streamlit. Eso es a proposito: la partida se puede
probar desde la terminal (mira test_juego.py) sin levantar la interfaz.
"""

from __future__ import annotations

import random

from game.modelos import (
    CLAVES,
    MENSAJES_DERROTA,
    Accion,
    Estadisticas,
    Evento,
    Mascota,
    Mensaje,
)


class Juego:
    """El orquestador: es el unico que sabe que pasa en un turno.

    Flujo de un turno (juego.realizar_accion):
        1. el jugador actua
        2. el tiempo cobra su parte (perdidas por turno)
        3. quiza salta un evento aleatorio
        4. la mascota dice como se encuentra
        5. se comprueba si alguna estadistica llego a 0
    """

    ESTADO_JUGANDO = "jugando"
    ESTADO_PERDIDO = "perdido"

    def __init__(self, config: dict) -> None:
        self.config = dict(config)
        self.mascota: Mascota | None = None
        self.turno: int = 0
        self.estado: str = self.ESTADO_JUGANDO
        self.motivo_derrota: str = ""
        self.historial: list[Mensaje] = []
        self.reiniciar()

    @classmethod
    def iniciar(cls, config: dict) -> Juego:
        """Punto de entrada que usa la interfaz de Streamlit."""
        return cls(config)

    # -- Estado -------------------------------------------------------------
    def reiniciar(self) -> None:
        """Vuelve a empezar la partida con los valores iniciales del config."""
        config = self.config
        self.mascota = Mascota(
            nombre=config["nombre_mascota"],
            estadisticas=Estadisticas(
                hambre=config["hambre_inicial"],
                energia=config["energia_inicial"],
                felicidad=config["felicidad_inicial"],
                maximo=config["maximo_estadistica"],
            ),
        )
        self.turno = 0
        self.estado = self.ESTADO_JUGANDO
        self.motivo_derrota = ""
        self.historial = []
        self._registrar(
            Mensaje.crear(
                f"¡Hola! Soy {self.mascota.nombre} y necesito que me cuides. 🐾",
                "👋",
                "sistema",
            )
        )

    def esta_jugando(self) -> bool:
        return self.estado == self.ESTADO_JUGANDO

    # -- Turno --------------------------------------------------------------
    def realizar_accion(self, accion: Accion) -> str:
        """Aplica la accion del jugador y hace avanzar el reloj un turno.

        Devuelve lo que ha dicho la mascota, para que la interfaz pueda
        decidir si necesita repintar algo.
        """
        if not self.esta_jugando():
            return ""

        # 1. El jugador actua: la mascota responde y cambian los numeros.
        self._registrar(
            Mensaje.crear(self.mascota.reaccionar_accion(accion), accion.icono(), "accion")
        )
        self._aplicar_deltas(accion.deltas(self.config))

        # 2-4. Pasa el tiempo, igual que en un Tamagotchi real.
        self.avanzar_turno()

        # 5. Ultima comprobacion del turno: si llego a 0, se escapa.
        self.comprobar_derrota()
        return self.mensaje_actual().texto

    def avanzar_turno(self) -> None:
        """Un turno = tiempo que pasa. Siempre perjudica un poco."""
        self.turno += 1
        self.mascota.turno = self.turno

        # El hambre y el cansancio no paran, te los haga o no te los haga.
        for clave in CLAVES:
            self.mascota.estadisticas.disminuir(clave, self.config[f"perdida_turno_{clave}"])

        evento = self.aplicar_evento()
        if evento is not None:
            self._registrar(Mensaje.crear(evento.texto(), evento.icono, "evento"))

        self._registrar(Mensaje.crear(self._saludo(), self._emoji(), "estado"))

    def aplicar_evento(self) -> Evento | None:
        """Lanza un evento con la probabilidad configurada.

        Devuelve None si este turno no pasa nada, que es lo normal:
        el evento es una sorpresa, no la regla.
        """
        if random.random() >= self.config["probabilidad_evento"]:
            return None
        evento = Evento.generar_aleatorio()
        evento.aplicar(self.mascota.estadisticas)
        return evento

    def comprobar_derrota(self) -> bool:
        """Si cualquier estadistica toca 0, la mascota se escapa.

        Se mira siempre la estadistica mas baja, asi el motivo de la
        derrota es concreto ("se fue por hambre") y no un simple "perdiste".
        """
        estadisticas = self.mascota.estadisticas
        culpable = estadisticas.mas_bajas()
        if estadisticas.valor(culpable) > 0:
            return False

        self.estado = self.ESTADO_PERDIDO
        self.mascota.viva = False
        self.motivo_derrota = culpable
        self._registrar(Mensaje.crear(MENSAJES_DERROTA[culpable], "💀", "derrota"))
        return True

    # -- Mensajes -----------------------------------------------------------
    def mensaje_actual(self) -> Mensaje:
        """La ultima linea del chatter (la que se pinta grande)."""
        if self.historial:
            return self.historial[-1]
        return Mensaje.crear("", "🐾", "sistema")

    def _saludo(self) -> str:
        return self.mascota.saludo(self.config["umbral_bajo"], self.config["umbral_alto"])

    def _emoji(self) -> str:
        return self.mascota.emoji(self.config["umbral_bajo"], self.config["umbral_alto"])

    # -- Utilidades internas ------------------------------------------------
    def _aplicar_deltas(self, deltas: dict) -> None:
        """Traduce un diccionario {estadistica: cantidad} a la mascota."""
        for clave, cantidad in deltas.items():
            if cantidad >= 0:
                self.mascota.estadisticas.aumentar(clave, cantidad)
            else:
                self.mascota.estadisticas.disminuir(clave, -cantidad)

    def _registrar(self, mensaje: Mensaje) -> None:
        """Añade una linea al historial respetando el tamaño configurado."""
        mensaje.turno = self.turno
        self.historial.append(mensaje)
        limite = self.config["turnos_historial"]
        if len(self.historial) > limite:
            self.historial = self.historial[-limite:]
