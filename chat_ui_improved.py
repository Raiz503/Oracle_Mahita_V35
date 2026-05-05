# Improved Chat Interface for Oracle_Mahita_V35

class ChatUI:
    def __init__(self):
        self.messages = []  # List to store messages  
        self.create_chat_ui()  

    def create_chat_ui(self):
        import tkinter as tk

        self.root = tk.Tk()
        self.root.title("Chat Interface")

        # Create scrollable messages area
        self.messages_area = tk.Text(self.root, height=25, width=50, wrap='word')
        self.messages_area.pack(expand=True, fill='y')
        self.messages_area.config(state=tk.DISABLED)  

        # Entry field for user input
        self.user_input = tk.Entry(self.root, width=50)
        self.user_input.pack(side='bottom', fill='x')

        # Send button
        self.send_button = tk.Button(self.root, text='Send', command=self.send_message)
        self.send_button.pack(side='bottom')

        self.root.mainloop()

    def send_message(self):
        user_message = self.user_input.get()
        if user_message:
            self.messages.append(f'User: {user_message}')
            self.update_chat_display()
            self.user_input.delete(0, tk.END)  

    def update_chat_display(self):
        self.messages_area.config(state=tk.NORMAL)
        self.messages_area.insert(tk.END, '\n'.join(self.messages) + '\n')
        self.messages_area.config(state=tk.DISABLED)
        self.messages_area.yview(tk.END)  # Auto-scroll to the bottom

if __name__ == '__main__':
    ChatUI()