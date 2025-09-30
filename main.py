from dash import Dash, html, dcc, Input, Output, State
import datetime
o_datetime = datetime.datetime.strptime('1976-07-02 23:30:00', '%Y-%m-%d %H:%M:%S')

app = Dash()
server=app.server # <-- belangrijk voor deployment
app.layout = html.Div([
    dcc.Store(id='cl_allowed_audiofiles_store', data=''),
    html.Button(id='cl_btn_loaddata_into_dccstore', children='Load Data', n_clicks=0),
    html.Button(id='cl_btn_select_audiofolder', children="Kies map", n_clicks=0),
    dcc.Dropdown(id="cl_drp_audiofilelist", placeholder="Selecteer een audio-bestand"),
    html.P(id="cl_audio_errormessage", style={"color": "red"}),
    html.Audio(id="cl_audioplayer", controls=True),
    #html.Div(id="js_trigger_audiofiles_are_in_store", **{"data-files": ""}),
    html.Div(id="cl_begintime", children=o_datetime),
    html.Div(id="cl_ann", children='no audiofile loaded'),
    dcc.Input(id="cl_hidden_selected_label", type="text", value="", style={"display": "none"}),
    html.Div(id="cl_debug_selected_label", children = "cl_debug_selected_label: hier komt debuginfo van geselecteerde label"),
    html.Div(id="cl_debug_raw_message", children = "cl_debug_raw_message: hier komt debuginfo van raw message"),
    html.Div(id="cl_debug_dcc_filled", children = "dccstore empty"),
    dcc.Interval(id='cl_interval', interval=1000)
])
@app.callback(
    Output('cl_allowed_audiofiles_store', 'data'),
    Input('cl_btn_loaddata_into_dccstore', 'n_clicks'),
    prevent_initial_call=True
)
def update_output(n_clicks):
    mijn_bestanden = [
        {'label': '2025-05-26 09:30:21', 'value': '093021_093029.mp3'},
        {'label': '2025-05-26 09:35:08', 'value': '093508_093604.mp3'},
        {'label': '2025-05-26 09:39:46', 'value': '093946_100946.mp3'}
    ]
    return mijn_bestanden

@app.callback(
    Output('cl_debug_dcc_filled', 'children'),
    Input('cl_allowed_audiofiles_store', 'data'),
    prevent_initial_call=True
)
def update_output(data):
    return "er zijn audiolijst-gegevens ingeladen"

app.clientside_callback(
    """
    // open a folder with audiofiles on the client
    // make a list of audiofiles in the folder
    // check if the audiofiles in the folder are the same as in the toegestaneBestanden
    // if so, push the list to a dash core component  
    async function(n_clicks, toegestaneBestanden) {
        if (!n_clicks) return [[], ""];

        try {
            const dirHandle = await window.showDirectoryPicker();
            const toegestaneMap = new Map(toegestaneBestanden.map(item => [item.value, item.label]));
            const audioFiles = [];

            for await (const entry of dirHandle.values()) {
                if (
                    entry.kind === 'file' &&
                    /\.(mp3|wav)$/i.test(entry.name) &&
                    toegestaneMap.has(entry.name)
                ) {
                    const file = await entry.getFile();
                    const url = URL.createObjectURL(file);
                    audioFiles.push({ label: toegestaneMap.get(entry.name), value: url });
                }
            }

            if (audioFiles.length === 0) {
                return [[], "⚠️ Geen toegestane audio-bestanden gevonden"];
            }
            console.log(audioFiles.value)
            return [audioFiles, ""];  // dropdown options, audio src, error msg, label
        } catch (err) {
            console.error("Folder selection cancelled or failed:", err);
            return [[], "⚠️ Folder selection was cancelled or failed."];
        }
    }
    """,
    [Output("cl_drp_audiofilelist", "options"),
     Output("cl_audio_errormessage", "children")],
    [Input("cl_btn_select_audiofolder", "n_clicks"),
     State('cl_allowed_audiofiles_store', 'data')])

app.clientside_callback(
    """
    function(selectedAudioUrl, options) {
        if (!selectedAudioUrl || !options) {
            return ["", ""];
        }

        // Zoek het label dat hoort bij de geselecteerde blob-url
        const match = options.find(opt => opt.value === selectedAudioUrl);
        const label = match ? match.label : "";
        // label must be iso 8601 format
        let isotimelabel=label;
        if (label.includes(" ")){
        isotimelabel = label.replace(" ", "T");
        }
        return [selectedAudioUrl, isotimelabel];
    }
    """,
    [Output("cl_audioplayer", "src"),
     Output("cl_begintime", "children")],
    [Input("cl_drp_audiofilelist", "value"),
     State("cl_drp_audiofilelist", "options")]
)
app.clientside_callback(
    """
    function TrackCurrentTime(jsbegintime, jsinterval) {
    // HELP-FUNCTIONS
    function addSeconds(date, seconds) {
        date.setSeconds(date.getSeconds() + seconds);
        return date;
    }

    function getLocalISOString(date) {
        const offset = date.getTimezoneOffset();
        const offsetAbs = Math.abs(offset);
        const isoString = new Date(date.getTime() - offset * 60 * 1000).toISOString();
        return `${isoString.slice(0, -1)}${offset > 0 ? '-' : '+'}${String(Math.floor(offsetAbs / 60)).padStart(2, '0')}:${String(offsetAbs % 60).padStart(2, '0')}`;
    }

    // MAIN FUNCTION
    const myaudio = document.getElementById("cl_audioplayer");
    const time_cur_s = Math.round(myaudio.currentTime);

    // Controleer of jsbegintime geldig is
    let begintijd = jsbegintime;
    if (!begintijd || begintijd.trim() === "") {
        // Standaardwaarde instellen (bijv. 1 januari 2000 om 00:00:00)
        begintijd = "2000-01-01T00:00:00";
    }

    const o_time_start = new Date(begintijd);
    const o_ann = addSeconds(o_time_start, time_cur_s);
    const txt_ann = getLocalISOString(o_ann).substring(0, 19);

    console.log("Begintijd:", begintijd, "→ Huidige tijd:", txt_ann);

    return txt_ann;
}
    """,
    Output('cl_ann', 'children'),
    Input('cl_begintime', 'children'),
    Input('cl_interval', 'n_intervals'),  # every dcc.interval a new value is taken from audio component
)
if __name__ == '__main__':
    app.run(debug=True)
