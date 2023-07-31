import pandas as pd
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox as msg
from liquidaciones.liquidaciones_cmd import main as main_liquidaciones


class LiquidacionesApp:

    def __init__(self, root):

        self.root = root
        self.file_name = ''
        self.f = Frame(self.root,
                       height=100,
                       width=250)

        # Place the frame on root window
        self.f.pack()

        # Creating label widgets
        self.message_label = Label(self.f,
                                   text='Procesar un fichero de liquidaciones de gesfincas',
                                   font=('Arial', 19), #, 'underline'),
                                   # fg='Green'
                                   )
        self.message_label2 = Label(self.f,
                                    text='Unifica todas las pestañas en un fichero con dos pestañas, una para ingresos '
                                         'y otra para gastos',
                                    font=('Arial', 14), #, 'underline'),
                                    #fg='Red'
                                    )

        # Buttons
        self.convert_button = Button(self.f,
                                     text='Seleccionar y procesar fichero...',
                                     font=('Arial', 14),
                                     # bg='Orange',
                                     # fg='Black',
                                     command=self.browse_file)
        self.exit_button = Button(self.f,
                                  text='Salir',
                                  font=('Arial', 14),
                                  # bg='Red',
                                  # fg='Black',
                                  command=root.destroy)

        # Placing the widgets using grid manager
        self.message_label.grid(row=1, column=0, columnspan=2)
        self.message_label2.grid(row=2, column=0, columnspan=2)
        self.convert_button.grid(row=3, column=0,
                                 padx=0, pady=15)
        self.exit_button.grid(row=3, column=1,
                              padx=10, pady=15)

    def browse_file(self):
        self.file_name = filedialog.askopenfilename(# initialdir='/Desktop',
                                                    title='Seleccione el fichero de entrada',
                                                    filetypes=(('excel file', '*.xlsx'),
                                                               ('old excel file', '*.xls')))

        last_dot = self.file_name.rfind(".")
        out_filename = self.file_name[:last_dot] + "_" + "procesado" + self.file_name[last_dot:]
        try:
            main_liquidaciones(self.file_name, out_filename)
            msg.showinfo('Finalizado', f"Procesado el fichero '{self.file_name}' "
                                       f"y creado el fichero '{out_filename}'")
        except Exception as e:
            msg.showerror("Error interno", f"Error {e} procesando el fcihero {self.file_name}")


def main():
    # Driver Code
    root = Tk()
    root.title('Procesar un fichero de gesfincas')

    obj = LiquidacionesApp(root)
    # root.geometry('800x600')
    root.mainloop()


if __name__ == '__main__':
    main()
