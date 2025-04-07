from flask import Flask, render_template
from db_operations import get_giveaway_from_db
import os

app = Flask(__name__)

@app.route('/<message_id>')
def show_giveaway(message_id):
    giveaway = get_giveaway_from_db(message_id)
    
    if not giveaway:
        return "Giveaway not found", 404
    
    seconds = giveaway['Time']
    if seconds < 60:
        duration = f"{seconds} seconds"
    elif seconds < 3600:
        duration = f"{seconds//60} minutes"
    elif seconds < 86400:
        duration = f"{seconds//3600} hours"
    else:
        duration = f"{seconds//86400} days"
    
    data = {
        'title': giveaway['Title'],
        'host': giveaway['Hoster'],
        'duration': duration,
        'description': giveaway['Description'],
        'winner_count': len(giveaway['Winners']),
        'entries': len(giveaway['Entrants']),
        'participants': len(giveaway['Entrants']),
        'winners': giveaway['Winners']
    }
    
    return render_template('giveaway.html', 
                         giveaway=data,
                         winners=giveaway['Winners'],
                         entrants=giveaway['Entrants'])

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    app.run(host='0.0.0.0', debug=True)
