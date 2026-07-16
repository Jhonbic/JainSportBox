<template>
  <!-- Modal de Términos y Condiciones (contrato de adhesión v2.0 - 2026).
       Mantener TERMINOS_VERSION en sincronía con backend/routers/auth.py -->
  <div class="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" @click.self="$emit('cerrar')">
    <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col overflow-hidden">

      <!-- Header -->
      <div class="px-6 py-4 border-b border-gray-100 flex items-start justify-between gap-3">
        <div>
          <h2 class="text-lg font-extrabold text-gray-900">Jain Sport Box</h2>
          <p class="text-xs text-gray-500 font-semibold uppercase tracking-wide">
            Contrato de adhesión: términos, condiciones, exoneración de responsabilidad y consentimiento informado
          </p>
        </div>
        <button @click="$emit('cerrar')" class="text-gray-400 hover:text-gray-600 flex-shrink-0" aria-label="Cerrar">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>

      <!-- Cuerpo scrollable -->
      <div class="px-6 py-5 overflow-y-auto text-sm text-gray-700 space-y-5 leading-relaxed">

        <div class="bg-blue-50 border-l-4 border-blue-500 rounded-r-lg p-4 text-blue-900">
          <p class="font-bold mb-1">Información importante para el usuario:</p>
          <p>Al marcar la casilla electrónica de aceptación <strong>"Acepto los Términos, Condiciones y el Consentimiento
          Informado"</strong> en la plataforma o aplicación de <strong>Jain Sport Box</strong>, usted manifiesta de manera libre,
          consciente, expresa y previa que ha leído, entendido y aceptado en su totalidad las cláusulas descritas en este
          documento, el cual constituye un contrato de adhesión legalmente vinculante de acuerdo con la legislación de la
          República de Colombia.</p>
        </div>

        <section>
          <h3 class="font-extrabold text-gray-900 mb-2">1. Declaración de salud y asunción de riesgos inmanentes</h3>
          <p class="mb-2">El usuario declara bajo la gravedad de juramento que se encuentra en condiciones óptimas de salud física,
          mental y médica, sin impedimento alguno para realizar entrenamientos de fuerza, acondicionamiento físico, entrenamiento
          funcional o de alta intensidad dentro de las instalaciones de <strong>Jain Sport Box</strong>.</p>
          <ul class="list-disc pl-5 space-y-1.5">
            <li><strong>Certificación médica:</strong> el usuario certifica que no padece de ninguna patología cardiovascular,
            respiratoria, de presión arterial, ni cuenta con lesiones de tipo óseo, muscular, articular o ligamentario que puedan
            agravarse con la práctica del ejercicio físico.</li>
            <li><strong>Conocimiento del riesgo:</strong> el usuario comprende que la actividad deportiva y el uso de la maquinaria
            de entrenamiento conllevan un riesgo implícito que puede derivar en desgarros, fracturas, deshidratación, hernias,
            paro cardíaco, paro respiratorio, infarto agudo de miocardio, invalidez o incluso la muerte. El usuario asume de manera
            voluntaria y exclusiva todas las consecuencias derivadas de estos riesgos.</li>
            <li><strong>Deber de reporte inmediato:</strong> el usuario se compromete a detener inmediatamente cualquier práctica e
            informar al personal técnico o entrenadores si experimenta dolor agudo, mareo, fatiga extrema, debilidad, dificultad
            respiratoria o cualquier otro síntoma inusual antes, durante o después de su sesión de entrenamiento.</li>
            <li><strong>Valoración de aptitud física:</strong> el usuario reconoce que tiene el derecho y se le ha sugerido solicitar
            una valoración física o médica antes de comenzar sus entrenamientos. En caso de decidir entrenar sin la realización de
            dicha valoración previa, exonera a <strong>Jain Sport Box</strong> de cualquier desenlace clínico derivado de dicha omisión.</li>
          </ul>
        </section>

        <section>
          <h3 class="font-extrabold text-gray-900 mb-2">2. Exoneración de responsabilidad civil y penal</h3>
          <p class="mb-2">El usuario declara que libera, exime y mantiene indemne de toda responsabilidad civil (contractual o
          extracontractual), penal, administrativa o de cualquier otra índole a <strong>Jain Sport Box</strong>, a su propietario,
          representantes legales, entrenadores, colaboradores, arrendadores y personal administrativo, por cualquier tipo de lesión,
          enfermedad, accidente, pérdida de capacidad laboral, muerte, perjuicio directo o indirecto que pueda sufrir dentro del
          establecimiento o en el desarrollo de las actividades del gimnasio.</p>
          <p>En consecuencia, el usuario renuncia formalmente en este acto a iniciar cualquier tipo de acción judicial, demanda de
          indemnización de perjuicios, querella o reclamación legal de cualquier naturaleza en contra del centro de entrenamiento o
          sus vinculados por los conceptos aquí referidos.</p>
        </section>

        <section>
          <h3 class="font-extrabold text-gray-900 mb-2">3. Prohibición de sustancias médicas y ayudas ergogénicas</h3>
          <p class="mb-2">De conformidad con las normas de salud vigentes en Colombia, se prohíbe de manera estricta la
          comercialización, distribución, prescripción, promoción o consumo de cualquier tipo de medicamento, fármaco estimulante,
          esteroide anabólico u hormona dentro de las instalaciones de <strong>Jain Sport Box</strong>.</p>
          <p>El usuario reconoce que el centro de entrenamiento no recomienda ni avala el consumo de estas sustancias y exime a la
          organización de cualquier daño colateral, efecto adverso o descompensación médica derivada de su consumo individual.</p>
        </section>

        <section>
          <h3 class="font-extrabold text-gray-900 mb-2">4. Autorización para el uso y tratamiento de imagen</h3>
          <p class="mb-2">De conformidad con las leyes de propiedad intelectual colombianas, el usuario autoriza de manera expresa,
          libre, irrevocable y totalmente gratuita a <strong>Jain Sport Box</strong> para que capte su imagen, voz, retrato y
          fisonomía mediante registros de fotografía, video o audio durante las rutinas de ejercicio y actividades organizadas dentro
          o fuera de la sede deportiva.</p>
          <p>Dicho material podrá ser reproducido, editado, publicado y difundido con fines estrictamente publicitarios, informativos,
          comerciales y de marketing en los perfiles de redes sociales (Instagram, Facebook, TikTok, WhatsApp, entre otros), páginas
          web, folletos corporativos y demás canales de difusión del centro de entrenamiento, sin derecho a reclamar contraprestación
          económica, regalías ni compensaciones del uso del derecho de imagen.</p>
        </section>

        <section>
          <h3 class="font-extrabold text-gray-900 mb-2">5. Custodia de bienes personales y vehículos</h3>
          <p class="mb-2">El usuario es el único y exclusivo responsable del cuidado, protección y custodia de sus pertenencias
          personales (dinero, joyas, teléfonos móviles, dispositivos electrónicos, maletines, prendas de vestir, etc.) y vehículos
          estacionados en las inmediaciones de la sede de <strong>Jain Sport Box</strong>.</p>
          <p>El centro de entrenamiento no asume el deber de custodia de dichos elementos ni responderá en ningún caso por la pérdida,
          extravío, hurto, robo o daño de los mismos. El uso de casilleros (lockers) por parte del usuario es meramente temporal y se
          realiza bajo su propio riesgo, debiendo asegurar el compartimiento con su propio candado de seguridad.</p>
        </section>

        <section>
          <h3 class="font-extrabold text-gray-900 mb-2">6. Reglamento interno, comportamiento y convivencia</h3>
          <p class="mb-2">El usuario se compromete de forma obligatoria a acatar las normas internas de convivencia, higiene, etiqueta
          y seguridad establecidas por <strong>Jain Sport Box</strong>, las cuales incluyen de manera ilustrativa mas no limitativa:</p>
          <ul class="list-disc pl-5 space-y-1.5 mb-2">
            <li>Utilizar calzado y prendas deportivas adecuadas y limpias para el entrenamiento.</li>
            <li>Hacer uso obligatorio de toalla personal para limpiar el sudor en las máquinas y superficies de contacto.</li>
            <li>Organizar y regresar a su respectivo lugar los discos, mancuernas, colchonetas y demás implementos una vez finalizada su rutina.</li>
            <li>Mantener un trato respetuoso, cordial y de sana convivencia con el personal técnico, administrativo y demás afiliados del centro.</li>
          </ul>
          <p>El incumplimiento de estas normas, conductas de acoso, violencia física o verbal, o daños deliberados a la propiedad de la
          empresa, facultará a <strong>Jain Sport Box</strong> para cancelar la afiliación de manera unilateral, inmediata y permanente,
          reservándose el derecho de admisión sin obligación de realizar devoluciones o reembolsos monetarios.</p>
        </section>

        <section>
          <h3 class="font-extrabold text-gray-900 mb-2">7. Representación y cláusula especial para menores de edad</h3>
          <p class="mb-2">En el evento de que el usuario final de los servicios sea una persona menor de dieciocho (18) años de edad,
          quien efectúe el registro digital y marque la casilla de aceptación en la plataforma declara bajo gravedad de juramento que
          ostenta la calidad de padre, madre, tutor legal o representante autorizado del menor.</p>
          <p>En tal carácter, manifiesta conocer a plenitud el estado de salud del menor de edad, autoriza expresamente su ingreso a las
          disciplinas físicas dictadas en el establecimiento, asume de forma incondicional todos los riesgos físicos y legales descritos
          en este acuerdo, y consiente el tratamiento de sus datos personales e imagen bajo los parámetros éticos y legales que la
          Constitución Política de Colombia confiere para la protección del interés superior de los niños, niñas y adolescentes.</p>
        </section>

        <section>
          <h3 class="font-extrabold text-gray-900 mb-2">8. Tratamiento de datos personales (Habeas Data - Ley 1581 de 2012)</h3>
          <p class="mb-2">En cumplimiento de lo dispuesto por la Ley Estatutaria 1581 de 2012 y sus decretos reglamentarios, el usuario
          autoriza expresamente a <strong>Jain Sport Box</strong> para realizar la recolección, almacenamiento, uso, procesamiento,
          circulación e intercambio de sus datos personales (incluyendo nombre, cédula, teléfono, correo electrónico, datos de contacto
          de emergencia e imágenes captadas en cámaras de seguridad o registro publicitario).</p>
          <p>Las finalidades de este tratamiento corresponden a: (i) gestión administrativa de la afiliación; (ii) control de accesos y
          seguridad del establecimiento; (iii) facturación, contabilidad y recaudo; (iv) envío de comunicaciones informativas,
          promocionales, notificaciones de novedades y ofertas de mercadeo a través de llamadas, mensajes de texto SMS, WhatsApp o
          correo electrónico. El titular de los datos podrá ejercer sus derechos a conocer, actualizar, rectificar y suprimir su
          información contactando al canal de atención al cliente de la marca.</p>
        </section>

        <section>
          <h3 class="font-extrabold text-gray-900 mb-2">9. Declaración de origen de fondos</h3>
          <p>Bajo la gravedad de juramento, el usuario declara y garantiza que los recursos económicos utilizados para el pago de sus
          mensualidades, tiqueteras, anualidades o inscripciones en <strong>Jain Sport Box</strong> provienen de actividades lícitas y
          comerciales legítimas. Certifica que sus dineros no proceden del narcotráfico, lavado de activos, captación ilegal de dinero,
          financiación del terrorismo ni de ninguna conducta tipificada como delito dentro del Código Penal Colombiano.</p>
        </section>

        <p class="text-xs text-gray-400 text-center pt-2 border-t border-gray-100">
          Jain Sport Box · Florencia, Caquetá, Colombia · {{ TERMINOS_VERSION }}<br>
          Este documento constituye un acuerdo digital de adhesión de conformidad con la Ley 527 de 1999.
        </p>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3 bg-gray-50">
        <button @click="$emit('cerrar')"
          class="px-4 py-2.5 rounded-lg text-sm font-semibold text-gray-600 hover:bg-gray-100 transition-colors">
          Cerrar
        </button>
        <button @click="$emit('aceptar')"
          class="px-5 py-2.5 rounded-lg text-sm font-bold bg-red-600 hover:bg-red-700 text-white shadow-md transition-colors">
          He leído y acepto
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
// Versión del contrato mostrada y registrada al aceptar.
// Mantener en sincronía con TERMINOS_VERSION en backend/routers/auth.py.
const TERMINOS_VERSION = 'v2.0 - 2026'

defineEmits(['cerrar', 'aceptar'])
</script>
