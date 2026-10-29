using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace HistVault
{
    static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string scriptPath = Path.Combine(baseDir, "run_desktop.py");
                string pythonExe = FindPythonExecutable();

                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = pythonExe;
                psi.Arguments = string.Format("\"{0}\"", scriptPath);
                psi.WorkingDirectory = baseDir;
                psi.UseShellExecute = false;
                psi.CreateNoWindow = true;
                psi.WindowStyle = ProcessWindowStyle.Hidden;

                Process proc = Process.Start(psi);
                if (proc != null)
                {
                    proc.WaitForExit();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("HistVault launch error: " + ex.Message, "HistVault", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        static string FindPythonExecutable()
        {
            string[] candidates = new string[] {
                @"C:\Python313\pythonw.exe",
                @"C:\Python312\pythonw.exe",
                @"C:\Python311\pythonw.exe",
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), @"Programs\Python\Python313\pythonw.exe"),
                @"C:\Windows\py.exe",
                "pythonw.exe",
                "python.exe"
            };

            foreach (string c in candidates)
            {
                if (File.Exists(c)) return c;
            }
            return "pythonw.exe";
        }
    }
}
