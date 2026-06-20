# Proyecto: Sistema Operativo Personal Inteligente (Jarvis V1)

## Contexto General

Quiero desarrollar un asistente personal inteligente ejecutado en una tablet antigua que permanecerá encendida 24/7.

El objetivo NO es crear un chatbot tradicional.

El objetivo es construir el núcleo o cerebro de un sistema operativo personal capaz de:

* Recordar información importante sobre mí.
* Aprender progresivamente sobre mis hábitos, proyectos y objetivos.
* Responder preguntas utilizando memoria persistente.
* Gestionar distintos tipos de memoria.
* Servir como base para futuras automatizaciones.
* Permitir la incorporación futura de herramientas externas (YouTube music, Todoist, Google Calendar, Telegram, etc.).

La prioridad absoluta es diseñar una arquitectura sólida, modular, mantenible y escalable.

No quiero una solución experimental basada en múltiples agentes, AutoGPT o frameworks complejos.

Quiero una arquitectura limpia basada en FastAPI, SQLite, ChromaDB y DeepSeek API.

---
# Objetivos de la V1
(usar conda activate babas)
La primera versión debe enfocarse exclusivamente en el cerebro.

Debe ser capaz de:

1. Mantener memoria persistente.
2. Aprender nueva información relevante.
3. Actualizar conocimientos existentes.
4. Recuperar recuerdos relevantes mediante RAG.
5. Construir contexto personalizado.
6. Responder preguntas utilizando memoria y razonamiento.
7. Exponer una API REST lista para futuras interfaces.

No debe incluir aún:

* YouTube
* Telegram
* WhatsApp
* Automatizaciones complejas

Esas capacidades serán agregadas posteriormente como módulos independientes llamados "Extremidades".

---

# Stack Tecnológico

Backend(conda activate babas):

* Python 3.11+
* FastAPI
* Uvicorn

LLM:

* DeepSeek API (creas un .env)

Base de datos estructurada:

* SQLite

Memoria vectorial:

* ChromaDB

Embeddings:

* sentence-transformers

Configuración:

* Pydantic Settings
* dotenv

Logs:

* Python Logging

---

# Filosofía de Diseño

Separar completamente:

* Cerebro
* Memoria
* Herramientas
* Interfaces

El sistema debe seguir el siguiente modelo:

Usuario
↓
API
↓
Cerebro
↓
Memoria
↓
LLM

Las herramientas externas NO deben formar parte del cerebro.

---

# Arquitectura del Proyecto

jarvis/

├── app/
│
├── api/
│   ├── chat.py
│   ├── memory.py
│   ├── profile.py
│   └── health.py
│
├── brain/
│   ├── reasoning.py
│   ├── planner.py
│   ├── context_builder.py
│   ├── memory_extractor.py
│   └── response_formatter.py
│
├── memory/
│   ├── profile/
│   │   └── sqlite.db
│   │
│   ├── episodic/
│   │   └── chroma/
│   │
│   ├── knowledge/
│   │   ├── pdf/
│   │   ├── notes/
│   │   └── documents/
│   │
│   └── skills/
│
├── tools/
│
├── services/
│
├── models/
│
├── schemas/
│
├── config/
│
├── logs/
│
├── tests/
│
└── main.py

---

# Sistema de Memorias

Implementar cuatro tipos de memoria.

## 1. Memoria de Perfil

SQLite

Información permanente o semipermanente.

Ejemplos:

* Nombre
* Objetivos
* Proyectos
* Intereses
* Tecnologías favoritas
* Hábitos

Ejemplos reales:

"Rodrigo estudia Ingeniería en Sistemas"

"Rodrigo trabaja en autotronica, le gustas los autos y la tecnologia"

"Quiere mejorar disciplina"

"Está aprendiendo Python"

---

## 2. Memoria Episódica

ChromaDB

Guardar experiencias y eventos.

Ejemplos:

"Terminó el módulo GPS"

"Resolvió un problema con su novia"

"Trabajó 3 horas en Python"

Debe almacenar:

* Fecha
* Contenido
* Embedding
* Categoría

---

## 3. Base de Conocimiento

RAG documental.

Documentos externos:

* PDFs
* Manuales
* Notas
* Apuntes

Debe permitir búsquedas semánticas.

---

## 4. Memoria Procedimental

Skills.

Describe cómo hacer algo.

Ejemplos:

crear_reporte_linkgps.yaml

planificar_estudio.yaml

resolver_error_laravel.yaml

No almacena información.

Almacena procedimientos.

---

# Aprendizaje Automático de Memorias

Cada mensaje recibido debe pasar por un extractor de memoria.

Pipeline:

Mensaje Usuario
↓
Memory Extractor
↓
Clasificación
↓
Guardar si es relevante

No almacenar conversaciones completas.

No almacenar mensajes triviales.

Solo guardar información útil.

Ejemplo:

Usuario:
"Estoy aprendiendo Angular"

Resultado:

Actualizar perfil:

learning_framework = Angular

---

# Construcción de Contexto

Antes de llamar al modelo:

1. Buscar datos relevantes en SQLite.
2. Buscar recuerdos relevantes en ChromaDB.
3. Buscar documentos relacionados.
4. Construir contexto consolidado.
5. Enviar contexto a DeepSeek.

---

# Endpoint Principal

POST /chat

Entrada:

{
"message": "¿Qué sabes de mí?"
}

Proceso:

1. Recuperar memorias relevantes.
2. Construir contexto.
3. Consultar DeepSeek.
4. Actualizar memoria si corresponde.
5. Responder.

---

# Formato de Respuesta

Nunca responder texto plano internamente.

Todas las respuestas deben estar estructuradas.

Ejemplo:

{
"type": "answer",
"message": "...",
"confidence": 0.95,
"memory_used": [
"profile",
"episodic"
]
}

---

# Endpoints Iniciales

GET /health

POST /chat

GET /profile

PUT /profile

GET /memory

DELETE /memory/{id}

POST /knowledge/upload

GET /knowledge/search

---

# Sistema de Herramientas Futuro

Preparar una arquitectura extensible.

Crear carpeta:

tools/

En el futuro contendrá:

youtube.py

spotify.py

todoist.py

calendar.py

linkgps.py

telegram.py

android.py

Cada herramienta deberá implementar una interfaz común.

El cerebro nunca deberá depender directamente de ninguna herramienta.

---

# Requisitos de Calidad

Aplicar:

* Clean Architecture
* SOLID
* Dependency Injection
* Tipado fuerte
* Documentación OpenAPI
* Logging estructurado
* Manejo centralizado de errores
* Testing básico

---

# Resultado Esperado

Construir una primera versión funcional del cerebro de un sistema operativo personal inteligente capaz de recordar, aprender, recuperar conocimiento mediante RAG y responder preguntas personalizadas utilizando DeepSeek API, SQLite y ChromaDB, dejando preparada una arquitectura modular para incorporar futuras extremidades sin necesidad de rediseñar el núcleo.
