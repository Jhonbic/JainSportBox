using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Windows.Forms;

namespace HuelleroBridge
{
    internal static class Program
    {
        // ===== Thread Execution State (evita idle/sleep del sistema) =====
        [DllImport("kernel32.dll")]
        private static extern uint SetThreadExecutionState(uint esFlags);

        private const uint ES_CONTINUOUS       = 0x80000000;
        private const uint ES_SYSTEM_REQUIRED  = 0x00000001;

        // ===== Detach console (FreeConsole) =====
        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern bool FreeConsole();

        private static void EvitarSuspensionSistema()
        {
            try { SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED); }
            catch { }
        }

        // Redirige Console.Out/Error a un archivo de log (junto al .exe) y luego
        // suelta la consola con FreeConsole(). El proceso queda como app de fondo.
        // Las llamadas a Console.WriteLine existentes siguen funcionando: ahora
        // van a bridge.log en lugar de a la ventana.
        private static void RedirigirLogsYSoltarConsola()
        {
            try
            {
                var dir     = AppDomain.CurrentDomain.BaseDirectory;
                var logPath = Path.Combine(dir, "bridge.log");

                // append mode + autoflush para que se vea en tiempo real con `Get-Content -Wait`
                var stream = new FileStream(logPath, FileMode.Append, FileAccess.Write, FileShare.Read);
                var writer = new StreamWriter(stream, new UTF8Encoding(false)) { AutoFlush = true };

                writer.WriteLine();
                writer.WriteLine($"===== Bridge iniciado {DateTime.Now:yyyy-MM-dd HH:mm:ss} =====");

                Console.SetOut(writer);
                Console.SetError(writer);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[WARN] No se pudo redirigir logs: {ex.Message}");
            }

            try { FreeConsole(); } catch { }
        }

        // Deja en bridge.log toda excepción que llegue sin atrapar. NO evita que el
        // proceso muera —una excepción en un hilo del ThreadPool lo termina igual—,
        // pero hasta acá el log simplemente se cortaba a mitad y no había forma de
        // saber si el bridge había crasheado, si lo habían cerrado, o si el PC se
        // había reiniciado. Con esto la caída deja evidencia.
        private static void RegistrarHandlersDeExcepcion()
        {
            AppDomain.CurrentDomain.UnhandledException += (_, e) =>
            {
                Console.WriteLine($"[FATAL] Excepción no controlada ({DateTime.Now:yyyy-MM-dd HH:mm:ss}):");
                Console.WriteLine(e.ExceptionObject?.ToString() ?? "(sin detalle)");
                Console.WriteLine($"[FATAL] ¿Termina el proceso? {e.IsTerminating}");
            };

            // Excepciones del hilo de UI: por acá llegan los callbacks COM del SDK. El
            // default de WinForms es abrir un diálogo modal, y ese es el peor desenlace
            // posible en una PC sin nadie mirando — el proceso queda VIVO pero colgado,
            // así que el watchdog no lo relanza y el lector no responde.
            Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
            Application.ThreadException += (_, e) =>
            {
                Console.WriteLine($"[FATAL] Excepción en el hilo de UI ({DateTime.Now:yyyy-MM-dd HH:mm:ss}):");
                Console.WriteLine(e.Exception?.ToString() ?? "(sin detalle)");

                // Se sale a propósito en vez de seguir. Si algo reventó en un callback
                // del SDK no hay forma de saber si la captura quedó sana, y un bridge
                // que corre con el lector mudo es peor que uno caído: el watchdog lo
                // levanta en 3 minutos a un estado conocido, y queda el stacktrace de
                // arriba para saber qué pasó. Si esto derivara en reinicios en bucle,
                // se vería en watchdog.log — que también es información.
                Console.WriteLine("[FATAL] Cerrando para que el watchdog reinicie a un estado limpio.");
                Application.Exit();
            };
        }

        // Una segunda instancia no puede tomar los puertos 8001/8765 y muere apenas
        // arranca, pero antes de morir deja logs en el mismo bridge.log y confunde el
        // diagnóstico. Peor: el watchdog corre cada 3 minutos y necesita que "hay
        // proceso" signifique "hay UN proceso sano".
        private static System.Threading.Mutex _instancia;

        private static bool YaHayOtraInstancia()
        {
            bool nuevo;
            _instancia = new System.Threading.Mutex(true, @"Global\JainSportBox.HuelleroBridge", out nuevo);
            return !nuevo;
        }

        [STAThread]
        private static void Main()
        {
            EvitarSuspensionSistema();

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            Console.Title = "JainSportBox - Huellero Bridge";
            Console.WriteLine("=== Huellero Bridge (DigitalPersona U.are.U 4500) ===");

            // La comprobación va ANTES de redirigir el log, y no es un detalle de
            // orden: el log se abre con FileShare.Read, así que la instancia que
            // sobra no puede escribir en él y su mensaje se perdería. Acá todavía
            // hay consola real — que es justo lo que ve quien acaba de hacer doble
            // clic al exe, o sea la persona que necesita leerlo. De paso, una
            // instancia rechazada no ensucia bridge.log con un "Bridge iniciado"
            // que después haría creer que hubo un reinicio.
            if (YaHayOtraInstancia())
            {
                Console.WriteLine("Ya hay otra instancia del bridge corriendo. Esta se cierra.");
                System.Threading.Thread.Sleep(3000);
                return;
            }

            Console.WriteLine("La ventana de consola se cerrará en breve.");
            Console.WriteLine("Logs en tiempo real: bridge.log (junto al .exe).");

            RedirigirLogsYSoltarConsola();
            RegistrarHandlersDeExcepcion();

            // Deja claro en el log a qué backend apunta el bridge y si el secreto
            // está definido. Crítico para diagnosticar fallos de enrolamiento/asistencia.
            Console.WriteLine($"[CONFIG] ApiBase      = {BridgeConfig.ApiBase}");
            Console.WriteLine($"[CONFIG] BridgeSecret = {(string.IsNullOrEmpty(BridgeConfig.BridgeSecret) ? "(vacío)" : "(definido)")}");

            // Fecha de compilación del exe en ejecución: permite confirmar en el log
            // qué build está corriendo (clave cuando una actualización "no toma").
            try
            {
                var exePath = System.Reflection.Assembly.GetExecutingAssembly().Location;
                Console.WriteLine($"[CONFIG] Build        = {File.GetLastWriteTime(exePath):yyyy-MM-dd HH:mm:ss} ({exePath})");
            }
            catch { }

            var state = new EnrollmentState();

            var hub = new WebSocketHub("ws://0.0.0.0:8765");
            hub.Start();
            Console.WriteLine("[WS] Escuchando en ws://localhost:8765");

            var form = new BridgeForm(state, hub);

            // HttpApi necesita referencia al capture para cargar templates en verify mode
            // BridgeForm crea el capture; lo pasamos después de construir el form
            var api = new HttpApi(state, form.Capture, form.Relay, port: 8001);
            api.Start();

            Console.CancelKeyPress += (_, e) => { e.Cancel = true; Application.Exit(); };

            // El try acá cubre lo que revienta durante el message pump y que los
            // handlers de arriba no alcanzan a interceptar; sin él, la salida quedaba
            // sin registro de ningún tipo.
            try
            {
                Application.Run(form);
                Console.WriteLine($"[INFO] Bridge detenido normalmente {DateTime.Now:yyyy-MM-dd HH:mm:ss}.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[FATAL] El bridge terminó por una excepción ({DateTime.Now:yyyy-MM-dd HH:mm:ss}):");
                Console.WriteLine(ex.ToString());
                throw;
            }
        }
    }
}
