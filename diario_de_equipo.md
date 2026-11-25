# Diario de equipo
<div align="center">
  <img src="https://github.com/user-attachments/assets/ef452e8f-e6bc-4239-81e9-59a977e65a07" width="450" alt="image"/>
 
  ### **Evolución y Gestión de la Configuración**    
  ### **Asignaturas-hub**      
 
 
  | **Integrantes:** |
  | :-----: |
  | Gustavo Delgado Álvarez
  José Antonio Reina Navarro
  Laura Cubero Sánchez
  Alejandro León Martín Lama
  Henrique Rebollo Padovani |


</div>


<div align="justify">


# Índice


1. [Reunión del lunes 9 de noviembre](#reunión-del-lunes-9-de-noviembre)


2. [Decisiones del domingo 22 de noviembre](#temas-tratados-y-decisiones-del-domingo-22-de-noviembre)


3. [Reunión del lunes 23 de noviembre](#reunión-del-lunes-23-de-noviembre-clase-de-laboratorio)




# Reunión del lunes 9 de noviembre
**Fecha:** 09/11/2026  
**Hora de inicio y finalización:** 15:30 - 17:20  
**Tipo de reunión / medio utilizado:** presencial  
**Participantes:**  
- Gustavo Delgado Álvarez  
- José Antonio Reina Navarro
- Laura Cubero Sánchez
- Alejandro León Martín Lama
- Henrique Rebollo Padovani  


Durante la reunión se revisaron y concretaron diferentes aspectos de la organización y planificación del proyecto UVLHub, a raíz de las cuestiones planteadas previamente por el profesor sobre el Acta Fundacional.


## Los principales temas tratados fueron:


1. **Tipo de hub**: se debatió qué información contendrá el hub y qué formato se utilizaría para almacenar e intercambiar los datos.
2. **Comunicación**: se revisaron las herramientas que utilizará el equipo para comunicarse, celebrar reuniones y compartir documentos.
3. **Gestión del código**: se concretaron aspectos relativos a la organización de ramas, la nomenclatura de commits y la actualización del diario del equipo.
4. **Integración y despliegue continuos (CI/CD)**: se debatieron las pruebas automatizadas, las herramientas de análisis y formato del código, las revisiones de código, la gestión de releases y el entorno de preproducción de despliegue.
5. **Gestión de incidencias**
6. **Selección y reparto de Work Items**






## Decisiones tomadas


### 1. Tipo de hub  
- Utilizar como referencia los campos de información presentes en las páginas oficiales de las asignaturas.
- Utilizar JSON como formato de almacenamiento e intercambio de datos.


### 2. Comunicación  
- Mantener WhatsApp como herramienta de comunicación diaria e informal.
- Sustituir Microsoft Teams por Google Drive para el almacenamiento de archivos y Google Meet para la celebración de reuniones.


### 3. Gestión del código  
- No crear una única rama por work item.
- Adoptar el estándar `Conventional Commits` para unificar la nomenclatura de los mensajes de commit y usar `conventional-pre-commit` como hook para la validación automática de su cumplimiento.
- Actualizar el diario del equipo directamente desde la interfaz de GitHub, realizando los cambios sobre la rama `main`.


### 4. Integración y despliegue continuos (CI/CD)  
- Utilizar `Prettier` para mantener un formato uniforme del código y ejecutar su comprobación automáticamente mediante un Git hook.
- Establecer un sistema rotativo de revisiones de código antes de integrar las ramas en `trunk`, asignando al integrante encargado de revisar una rama la responsabilidad de realizar también su integración (merge) una vez aprobada.
- Realizar una release por cada Work Item completado.
- Priorizar el desarrollo del backend de cada funcionalidad antes de comenzar su frontend, con el objetivo de evitar que funcionalidades incompletas estén disponibles para los usuarios.
- No establecer el uso de `Feature Flags` como obligatorio, aunque se mantiene abierta la posibilidad de utilizarlos.
- Dejar la aplicación de `TDD` a criterio de cada desarrollador, sin imponerla como metodología obligatoria.
- Utilizar `Cloudflare` como plataforma de despliegue.


### 5. Gestión de incidencias
- Registrar las incidencias mediante Issues de GitHub.  
- Crear y utilizar una plantilla para homogeneizar la descripción de las incidencias.
- Delegar en el Project Manager la gestión del tablero del proyecto y la asignación de etiquetas a las incidencias.


### 6. Selección y reparto de Work Items  
- Se realizó la selección de los Work Items que desarrollaría cada integrante del equipo, teniendo en cuenta su dificultad y los trabajos obligatorios establecidos por la asignatura.
- Además, se acordó que el Work Item obligatorio de mayor dificultad, #178 ([issue #2 en asignaturas-hub](https://github.com/GustavoD1/asignaturas-hub/issues/2)), sería desarrollado conjuntamente por Gustavo, José Antonio y Laura. Estos se encargarán también de explicar al resto del equipo los aspectos relevantes de su implementación.


<div align="center">


| **Integrante** | **Dificultad** | **Referencia del WI asignado en uvlhub** | **Referencia del WI asignado en asignaturas-hub**|
|---|:---:|:---:|:---:|
| Alejandro León Martín Lama | Difícil | #204 | [#6](https://github.com/GustavoD1/asignaturas-hub/issues/6) |
| Henrique Rebollo Padovani | Fácil y difícil | #201, #202 | [#5](https://github.com/GustavoD1/asignaturas-hub/issues/5), [#4](https://github.com/GustavoD1/asignaturas-hub/issues/4) |
| Gustavo Delgado Álvarez | Medio | #188 | [#1](https://github.com/GustavoD1/asignaturas-hub/issues/1) |
| José Antonio Reina Navarro | Medio | #179 | [#7](https://github.com/GustavoD1/asignaturas-hub/issues/7) |
| Laura Cubero Sánchez | Medio | #177 (obligatorio) | [#3](https://github.com/GustavoD1/asignaturas-hub/issues/3) |


</div>




# Temas tratados y decisiones del domingo 22 de noviembre


- **Asignación de revisor:** cuando el autor de una Issue considere que su trabajo está preparado para ser integrado en la rama principal, deberá solicitar una revisión a otro integrante del equipo mediante un comentario en la propia Issue de GitHub, siguiendo la siguiente plantilla:




> **Review requested**: @nombre_de_usuario_correspondiente  
> **Branch:** nombre de la rama que se debe revisar. Por ejemplo: “ci/add-development-tests-workflow  
> **Commit(s):** URL, identificador o listado de los commits que deben revisarse. Por ejemplo: 2614e38




- **Decisión relativas a los workflows:** se decidió mantener los workflows iniciales proporcionados, añadiendo uno adicional destinado a ejecutar rápidamente las pruebas unitarias en las ramas distintas de `main`.
Además, se acordó modificar el workflow *CI_pytest.yml* para evitar que se ejecute cuando los únicos cambios realizados en la rama `main` afecten a la ruta correspondiente al diario del equipo, ya que no se considera necesario ejecutar las pruebas en ese caso.


- **Mensajes de los commits:** se acordó que los mensajes de los commits deberán incluir una referencia a la Issue de GitHub correspondiente, indicando así qué tarea o incidencia aborda cada cambio.


# Reunión del lunes 23 de noviembre (clase de laboratorio)
**Fecha:** 23/11/2026  
**Hora de inicio y finalización:** 15:30 - 17:00  
**Tipo de reunión / medio utilizado:** presencial  
**Participantes:**
- Gustavo Delgado Álvarez
- José Antonio Reina Navarro
- Laura Cubero Sánchez
- Alejandro León Martín Lama
- Henrique Rebollo Padovani


## Temas tratados y decisiones tomadas
Durante la sesión de laboratorio se llevó a cabo una revisión de los repositorios de otros equipos de la asignatura. A partir de esta actividad, se identificaron dos prácticas que se decidió incorporar a nuestra metodología de trabajo:


- **Establecimiento de prioridades de las Issues:** se acordó utilizar la opción *Priority* que ofrece el tablero Kanban de GitHub para establecer y visualizar el nivel de prioridad de las distintas Issues.


- **Gestión de las *sub-issues* :** se decidió dejar de establecer manualmente la relación entre las Issues principales y sus subtareas mediante referencias en sus descripciones. En su lugar, se utilizará la funcionalidad `Create sub-issues` que proporciona GitHub, permitiendo establecer directamente la relación jerárquica entre ambas.
De esta forma, se podrá visualizar con mayor claridad la división de los work items en subtareas y realizar un seguimiento más sencillo del estado de desarrollo de cada una.




</div>

