from flask import Flask, jsonify, request   
app = Flask(__name__)
def display_message():
    # get input from user
    user_input = request.args.get('message', 'Hello, World!')
    return f'You entered: {user_input}'         
@app.route('/') 
def home():
    # get input neatly and display the message  
    msg=display_message()
    return render_template('index.html', message=msg)
if __name__ == '__main__':
    app.run(debug=True)

de


  