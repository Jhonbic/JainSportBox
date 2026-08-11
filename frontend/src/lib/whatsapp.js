// Normalización de teléfonos para links de wa.me — fuente única del frontend.
//
// ESPEJA `normalizar_telefono()` de backend/whatsapp.py. Las dos reglas tienen que
// coincidir: si no, el recordatorio automático y el link manual le escriben a números
// distintos. Cambiar una obliga a cambiar la otra.
//
// Por qué "últimos 10 dígitos + 57" y no "agregar 57 si falta": así el resultado es el
// mismo venga el número como `3165300987`, `+57 316 530 0987` o `57 316 530 0987`. El
// admin carga el teléfono a mano desde el perfil y ninguno de esos formatos es raro.
//
// Existía una tercera variante en PlanesView que hacía solo `.replace(/\D/g,'')`, sin
// prefijo: con un número guardado como `3165300987` generaba `wa.me/3165300987`, que no
// es un número internacional válido y WhatsApp rechaza. Era el botón de "enviar el
// comprobante de pago", o sea la ruta por la que un socio nuevo paga.

/**
 * '57' + los últimos 10 dígitos. `null` si no hay al menos 10 dígitos.
 *
 * Devuelve `null` en vez de una cadena corta a propósito: un link a medio armar manda
 * a WhatsApp a una pantalla de error, y quien lo aprieta no sabe si falló el link o si
 * el gym no contesta. Con `null`, el llamador esconde el botón.
 */
export function telefonoWa(t) {
  const digitos = String(t ?? '').replace(/\D/g, '')
  return digitos.length < 10 ? null : '57' + digitos.slice(-10)
}

/** Link de wa.me con el texto ya codificado, o `null` si el teléfono no sirve. */
export function linkWa(telefono, mensaje) {
  const numero = telefonoWa(telefono)
  return numero ? `https://wa.me/${numero}?text=${encodeURIComponent(mensaje)}` : null
}
