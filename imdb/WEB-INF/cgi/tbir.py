from packages import *
from input_handler import InputHandler
from data_handler import DataHandler

class TBIR:
	def __init__(self):
		data_handle = None
		try:
			ui = InputHandler()
			database, search_term = ui.get_user_input_text()
			data_handle = DataHandler(database)
			data_handle.generate_output_tbir(search_term)
		except Exception as e:
			data_handle.enable_html()
			data_handle.draw_header()
			data_handle.write_into_logs(e)
			print('Something went wrong, ask server administrator to check logs<br> <a href="../"> Home Page </a>')
			data_handle.draw_footer()
		

tbir = TBIR()