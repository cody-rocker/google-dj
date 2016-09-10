package devhost.googledj;

import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.SharedPreferences;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Handler;
import android.os.PowerManager;
import android.support.v7.app.ActionBar;
import android.support.v7.app.AppCompatActivity;
import android.support.v7.widget.Toolbar;
import android.text.InputType;
import android.util.JsonReader;
import android.util.Log;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputMethodManager;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.ImageView;
import android.widget.SeekBar;
import android.widget.TextView;
import android.widget.Toast;

import java.io.BufferedReader;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.InetAddress;
import java.net.Socket;
import java.net.URL;
import java.util.Timer;
import java.util.TimerTask;

public class MainActivity extends AppCompatActivity implements View.OnClickListener {

    // Action Bar
    //ActionBar actionBar;
    Toolbar toolBar;

    // Network Icon
    MenuItem network_status;

    // Search Bar
    EditText edit_artistName;
    ImageButton connect_button;

    // Media Player Buttons
    ImageButton prev_button;
    ImageButton toggle_play_button;
    ImageButton next_button;

    // SeekBar slider
    SeekBar seekBar;
    TextView track_time;

    // Track metadata
    TextView track_info;
    ImageView album_art;

    // Socket client data
    private Socket socket;
    private int SERVER_PORT;
    private String SERVER_IP;
    private String CURRENT_HOST_ADDR;
    private String CURRENT_HOST_NAME;

    // Holds current state of media player
    private Boolean playing;

    // Holds client data sent to TCP socket server with possible reply format/content
    private String sendToServer;

    // Server response variables
    private String current_state;
    private String host;
    private String now_playing_artist;
    private String now_playing_title;
    private String now_playing_artRef;
    private String position;
    private String duration;
    private String time;
    private String seek_pos;

    // App Name for Debug Logging
    private static final String TAG = MainActivity.class.getSimpleName();

    // Persistent app data
    SharedPreferences mSharedPreferences;
    private static final String PREFS = "prefs";
    private static final String PREF_SERVER = "server";
    private static final String PREF_PORT = "port";

    // Run on Activity Start
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);


        // Tool bar stuff
        toolBar = (Toolbar) findViewById(R.id.toolbar);
        setSupportActionBar(toolBar);
        ActionBar actionBar = getSupportActionBar();
        if (actionBar != null) {
            actionBar.setHomeButtonEnabled(true);
            actionBar.setDisplayShowHomeEnabled(true);
            //actionBar.setDefaultDisplayHomeAsUpEnabled(true);
            actionBar.setIcon(android.R.drawable.ic_menu_sort_by_size);
            actionBar.setTitle("   Shuffle Artist");
            //actionBar.setDisplayShowTitleEnabled(false); //optional
        }

        edit_artistName = (EditText) findViewById(R.id.edit_artistName);
        edit_artistName.setOnEditorActionListener(new TextView.OnEditorActionListener() {
            @Override
            public boolean onEditorAction(TextView v, int actionId, KeyEvent event) {
                boolean handled = false;
                if (actionId == EditorInfo.IME_ACTION_GO) {
                    connect_button.performClick();
                    handled = true;
                }
                return handled;
            }
        });

        connect_button = (ImageButton) findViewById(R.id.connect_button);
        connect_button.setOnClickListener(this);
        prev_button = (ImageButton) findViewById(R.id.prev_button);
        prev_button.setOnClickListener(this);
        prev_button.setEnabled(false);
        toggle_play_button = (ImageButton) findViewById(R.id.toggle_play);
        toggle_play_button.setOnClickListener(this);
        toggle_play_button.setEnabled(false);
        next_button = (ImageButton) findViewById(R.id.next_button);
        next_button.setOnClickListener(this);
        next_button.setEnabled(false);

        // Status for current audio_stream
        playing = false;
        track_info = (TextView) findViewById(R.id.track_info);
        album_art = (ImageView) findViewById(R.id.album_art);
        seekBar = (SeekBar) findViewById(R.id.track_time);

        seekBar.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            int progress = 0;

            @Override
            public void onProgressChanged(SeekBar seekBar, int progressValue, boolean fromUser) {
                progress = progressValue;
                //Toast.makeText(getApplicationContext(), "Changing seekbar's progress", Toast.LENGTH_SHORT).show();

            }

            @Override
            public void onStartTrackingTouch(SeekBar seekBar) {
                //Toast.makeText(getApplicationContext(), "Started tracking seekbar", Toast.LENGTH_SHORT).show();
            }

            @Override
            public void onStopTrackingTouch(SeekBar seekBar) {
                Log.d(TAG, "Sending seek to position request to server.");
                sendToServer = "seek::" + progress;
                new SendCommand().execute("");
            }
        });
        track_time = (TextView) findViewById(R.id.track_time_text);

        // First Run
        displayWelcome();
        Log.d(TAG, "Synchronizing state with server...");

        // create a handler
        Handler syncHandler = new Handler();
        // create a timer task and pass the handler in
        ServerSyncTask syncTask = new ServerSyncTask(syncHandler);
        // use timer to run sync task every 3 seconds
        new Timer().scheduleAtFixedRate(syncTask, 0, 1000);
    }

    // Handle Button Presses on UI Thread
    @Override
    public void onClick(View v) {
        switch (v.getId()) {
            case R.id.connect_button:  // Play sample from Artist
                // Clear focus from EditText fields
                edit_artistName.clearFocus();
                // Force close soft keyboard
                InputMethodManager imm =(InputMethodManager)getSystemService(Context.INPUT_METHOD_SERVICE);
                imm.hideSoftInputFromWindow(v.getWindowToken(), 0);
                Toast.makeText(getApplicationContext(), "Searching...", Toast.LENGTH_LONG).show();
                sendToServer = "shuffle_artist::" + edit_artistName.getText().toString();
                Log.d(TAG, "Sending shuffle artist request to server.");
                edit_artistName.setText("");
                // Connect to the server
                new SendCommand().execute("");
                break;
            case R.id.prev_button:
                sendToServer = "play_prev";
                Log.d(TAG, "Sending play previous request to server.");
                // Connect to the server
                new SendCommand().execute("");
                break;
            case R.id.toggle_play:
                sendToServer = "toggle_play";
                Log.d(TAG, "Sending toggle play request to server.");
                toggle_play_button.setEnabled(false);
                // Connect to the server
                new SendCommand().execute("");
                break;
            case R.id.next_button:
                sendToServer = "play_next";
                Log.d(TAG, "Sending play next request to server.");
                // Connect to the server
                new SendCommand().execute("");
                break;
        }
    }

    // Inflate options menu layout
    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        // Inflate the menu; this adds items to the action bar if it is present.
        getMenuInflater().inflate(R.menu.menu_main, menu);
        return true;
    }

    // Get references to menu elements
    @Override
    public boolean onPrepareOptionsMenu(Menu menu) {
        network_status = menu.findItem(R.id.action_network);
        return super.onPrepareOptionsMenu(menu);
    }

    // Handle menu interactions
    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        int id = item.getItemId();
        switch (id) {
            case R.id.action_about:
                break;
            case R.id.action_settings:
                setServer();
                break;
            case R.id.action_network:
                if (CURRENT_HOST_ADDR != null) {
                    Toast toast = Toast.makeText(getApplicationContext(), CURRENT_HOST_NAME, Toast.LENGTH_LONG);
                    toast.setGravity(Gravity.TOP| Gravity.RIGHT, 5, 10);
                    toast.show();
                }
                break;
        }
        return super.onOptionsItemSelected(item);
    }

    // Update state of SeekBar slider
    public void updateSlider(String position, String duration) {
        if (position != null && duration != null) {
            seekBar.setProgress(Integer.parseInt(position));
            seekBar.setMax(Integer.parseInt(duration));
        }
    }

    // Update state of media player buttons
    public void updateButtons() {
        if (!playing) {
            toggle_play_button.setImageResource(android.R.drawable.ic_media_play);
        } else {
            toggle_play_button.setImageResource(android.R.drawable.ic_media_pause);
        }
    }

    // Set the current host address
    public void setServer() {
        AlertDialog.Builder new_host = new AlertDialog.Builder(this);
        new_host.setTitle("Add a new Host");
        new_host.setMessage("Please enter server information.");

        // Create EditText for entry
        final EditText server_ip = new EditText(this);
        server_ip.setRawInputType(InputType.TYPE_CLASS_NUMBER);
        server_ip.setHint(R.string.add_host_hint);
        new_host.setView(server_ip);

        // Make an "OK" button to save data
        new_host.setPositiveButton("OK", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {

                // Grab the EditText input
                String inputNewHost = server_ip.getText().toString();
                String[] parts = inputNewHost.split(":");
                String inputServerIp = parts[0];
                String inputServerPort = parts[1];

                // Put it into memory (don't forget to commit!)
                SharedPreferences.Editor e = mSharedPreferences.edit();
                e.putString(PREF_SERVER, inputServerIp);
                e.putString(PREF_PORT, inputServerPort);
                e.apply();

                // Confirm action to user
                Toast.makeText(getApplicationContext(), "Saved, " + inputServerIp + ":" + inputServerPort, Toast.LENGTH_LONG).show();
                // This is where you should set server variables
                CURRENT_HOST_ADDR = inputNewHost;
                SERVER_IP = inputServerIp;
                SERVER_PORT = Integer.parseInt(inputServerPort);
            }
        });

        // Make a "Cancel" button
        // that simply dismisses the alert
        new_host.setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {}
        });

        new_host.show();

    }

    // Register a New user or display Toast message with saved host
    public void displayWelcome() {
        // Access the device's key-value storage
        mSharedPreferences = getSharedPreferences(PREFS, MODE_PRIVATE);

        final String savedServer = mSharedPreferences.getString(PREF_SERVER, "");
        final String savedPort = mSharedPreferences.getString(PREF_PORT, "");
        if (savedServer.length() > 0) {
            // If the host is valid, display a Toast welcoming them
            Toast.makeText(this, "Synchronizing with, " + savedServer + ":" + savedPort, Toast.LENGTH_LONG).show();
            // This is where you should set server variables
            CURRENT_HOST_ADDR = savedServer + ":" + savedPort;
            SERVER_IP = savedServer;
            SERVER_PORT = Integer.parseInt(savedPort);
        } else {
            // otherwise, show a dialog to collect host data.
            setServer();
//            AlertDialog.Builder new_host = new AlertDialog.Builder(this);
//            new_host.setTitle("Add a new Host");
//            new_host.setMessage("Please enter server information.");
//
//            // Create EditText for entry
//            final EditText server_ip = new EditText(this);
//            server_ip.setRawInputType(InputType.TYPE_CLASS_NUMBER);
//            server_ip.setHint(R.string.add_host_hint);
//            new_host.setView(server_ip);
//
//            // Make an "OK" button to save data
//            new_host.setPositiveButton("OK", new DialogInterface.OnClickListener() {
//                @Override
//                public void onClick(DialogInterface dialog, int which) {
//
//                    // Grab the EditText input
//                    String inputNewHost = server_ip.getText().toString();
//                    String[] parts = inputNewHost.split(":");
//                    String inputServerIp = parts[0];
//                    String inputServerPort = parts[1];
//
//                    // Put it into memory (don't forget to commit!)
//                    SharedPreferences.Editor e = mSharedPreferences.edit();
//                    e.putString(PREF_SERVER, inputServerIp);
//                    e.putString(PREF_PORT, inputServerPort);
//                    e.apply();
//
//                    // Confirm action to user
//                    Toast.makeText(getApplicationContext(), "Saved, " + inputServerIp + ":" + inputServerPort, Toast.LENGTH_LONG).show();
//                    // This is where you should set server variables
//                    CURRENT_HOST_ADDR = inputNewHost;
//                    SERVER_IP = inputServerIp;
//                    SERVER_PORT = Integer.parseInt(inputServerPort);
//                }
//            });
//
//            // Make a "Cancel" button
//            // that simply dismisses the alert
//            new_host.setNegativeButton("Cancel", new DialogInterface.OnClickListener() {
//                @Override
//                public void onClick(DialogInterface dialog, int which) {}
//            });
//
//            new_host.show();
        }
    }

    // Update track_info and album_art
    public void updateMetadata(String artistName, String songTitle, String artRefUrl) {
        String metaData = artistName + " - "  + songTitle;
        if (!metaData.equals(track_info.getText().toString())) {
            Log.d(TAG, "Metadata has been updated.");
            track_info.setText(metaData);
            new ImageLoadTask(artRefUrl, album_art).execute();
        }
        track_info.setSelected(true);
    }

    // Add check to see if activity is being run in the background
    public Boolean checkDisplayState() {
        PowerManager powerManager = (PowerManager) getSystemService(POWER_SERVICE);
        // deprecated call for API 19 devices
        return powerManager.isScreenOn();
    }

    // Synchronize Android Client with Python Server in background (when display is on)
    private class SyncState extends AsyncTask<String, Void, String> {

        // Connect to TCP Socket Server
        @Override
        protected String doInBackground(String... params) {
            try {
                InetAddress serverAddr = InetAddress.getByName(SERVER_IP);
                socket = new Socket(serverAddr, SERVER_PORT);

                DataOutputStream dos = new DataOutputStream(socket.getOutputStream());
                dos.writeUTF(sendToServer);

                //read input stream for server response
                DataInputStream dis2 = new DataInputStream(socket.getInputStream());
                //create JsonReader object
                JsonReader jsonReader = new JsonReader(new InputStreamReader(dis2, "UTF-8"));
                //parse JsonObject
                jsonReader.beginObject();
                while (jsonReader.hasNext()) {
                    String key = jsonReader.nextName();
                    // Include all reply member labels here
                    switch (key) {
                        case "current_state":
                            current_state = jsonReader.nextString();
                            break;
                        case "host":
                            host = jsonReader.nextString();
                            break;
                        case "now_playing_artist":
                            now_playing_artist = jsonReader.nextString();
                            break;
                        case "now_playing_title":
                            now_playing_title = jsonReader.nextString();
                            break;
                        case "now_playing_artRef":
                            now_playing_artRef = jsonReader.nextString();
                            break;
                        case "position":
                            position = jsonReader.nextString();
                            break;
                        case "duration":
                            duration = jsonReader.nextString();
                            break;
                        case "time":
                            time = jsonReader.nextString();
                            break;
                        case "seek_pos":
                            seek_pos = jsonReader.nextString();
                            break;
                        default:
                            jsonReader.skipValue();
                            break;
                    }
                }
                jsonReader.endObject();

                //finish/close connection
                jsonReader.close();
                dis2.close();
                socket.close();

            } catch (IOException e1) {
                //e1.printStackTrace();
                //Log.d(TAG, "Client syncState socket connection Failed.");
                if (current_state != null) {
                    current_state = null;
                    //Log.d(TAG, current_state);
                }
            }
            return current_state;
        }

        // Update the GUI Thread Here
        @Override
        protected void onPostExecute(String result) {
            //act on server response
            if (result != null) {
                switch (result) {
                    case "SERVER_IDLE":
                        if (network_status != null) {
                            playing = false;
                            prev_button.setEnabled(false);
                            toggle_play_button.setEnabled(false);
                            next_button.setEnabled(false);
                            CURRENT_HOST_NAME = host;
                            track_info.setText("");
                            updateSlider("0", "100");
                            album_art.setImageResource(R.drawable.default_album_art);
                            network_status.setIcon(R.drawable.wlan_icon_blue);
                        }
                        break;
                    case "PLAY_STATE_PLAYING":
                        //Log.d(TAG, server_response[1]);
                        if (network_status != null) {
                            network_status.setIcon(R.drawable.wlan_icon_green);
                        }
                        playing = true;
                        prev_button.setEnabled(true);
                        toggle_play_button.setEnabled(true);
                        next_button.setEnabled(true);
                        CURRENT_HOST_NAME = host;
                        track_time.setText(time);
                        updateSlider(position, duration);
                        updateMetadata(now_playing_artist, now_playing_title, now_playing_artRef);
                        updateButtons();
                        break;
                    case "PLAY_STATE_PAUSED":
                        if (network_status != null) {
                            network_status.setIcon(R.drawable.wlan_icon_blue);
                        }
                        playing = false;
                        prev_button.setEnabled(true);
                        toggle_play_button.setEnabled(true);
                        next_button.setEnabled(true);
                        CURRENT_HOST_NAME = host;
                        updateMetadata(now_playing_artist, now_playing_title, now_playing_artRef);
                        updateButtons();
                        break;
                    default:
                        Log.d(TAG, "Unknown state.");
                        Log.d(TAG, result);
                        network_status.setIcon(R.drawable.wlan_icon_red);
                        break;
                }
            } else {
                //Log.d(TAG, "No response from server.");
                if (network_status != null) {
                    //Log.d(TAG, "wlan_icon_red");
                    //Toast.makeText(getApplicationContext(), R.string.server_response_NULL, Toast.LENGTH_LONG).show();
                    network_status.setIcon(R.drawable.wlan_icon_red);
                }
            }
        }
    }

    // Handle Client/User Commands to Server
    private class SendCommand extends AsyncTask<String, Void, String> {

        // Connect to TCP Socket Server
        @Override
        protected String doInBackground(String... params) {

            try {
                InetAddress serverAddr = InetAddress.getByName(SERVER_IP);
                socket = new Socket(serverAddr, SERVER_PORT);
                DataOutputStream dos = new DataOutputStream(socket.getOutputStream());
                dos.writeUTF(sendToServer);

                //read input stream for server response
                DataInputStream dis2 = new DataInputStream(socket.getInputStream());
                //create JsonReader object
                JsonReader jsonReader = new JsonReader(new InputStreamReader(dis2, "UTF-8"));
                //parse JsonObject
                jsonReader.beginObject();
                while (jsonReader.hasNext()) {
                    String key = jsonReader.nextName();
                    // Include all reply member labels here
                    switch (key) {
                        case "current_state":
                            current_state = jsonReader.nextString();
                            break;
                        case "host":
                            host = jsonReader.nextString();
                            break;
                        case "now_playing_artist":
                            now_playing_artist = jsonReader.nextString();
                            break;
                        case "now_playing_title":
                            now_playing_title = jsonReader.nextString();
                            break;
                        case "now_playing_artRef":
                            now_playing_artRef = jsonReader.nextString();
                            //Log.d(TAG, now_playing_artRef);
                            break;
                        case "position":
                            position = jsonReader.nextString();
                            break;
                        case "duration":
                            duration = jsonReader.nextString();
                            break;
                        case "time":
                            time = jsonReader.nextString();
                            break;
                        case "seek_pos":
                            seek_pos = jsonReader.nextString();
                            break;
                        default:
                            jsonReader.skipValue();
                            break;
                    }
                }
                jsonReader.endObject();

                //finish/close connection
                jsonReader.close();
                dis2.close();
                socket.close();

            } catch (IOException e1) {
                Log.d(TAG, "No response from server.");
                //e1.printStackTrace();
            }
            //return String
            return current_state;
        }

        // Update the GUI Thread Here
        @Override
        protected void onPostExecute(String result) {
            //act on server response
            if (result != null) {
                switch (result) {
                    case "PLAY_STATE_PLAYING":
                        //Log.d(TAG, server_response[0]);
                        // Display now playing
                        playing = true;
                        network_status.setIcon(R.drawable.wlan_icon_blue);
                        updateMetadata(now_playing_artist, now_playing_title, now_playing_artRef);
                        updateButtons();
                        break;
                    case "PLAY_STATE_PAUSED":
                        playing = false;
                        toggle_play_button.setEnabled(true);
                        updateButtons();
                        break;
                    case "SEARCH_EMPTY":
                        Toast.makeText(getApplicationContext(), "Search Empty.", Toast.LENGTH_LONG).show();
                        break;
                    case "END_OF_PLAYLIST":
                        Toast.makeText(getApplicationContext(), "End of Playlist.", Toast.LENGTH_LONG).show();
                        break;
                    case "START_OF_PLAYLIST":
                        Toast.makeText(getApplicationContext(), "Start of Playlist.", Toast.LENGTH_LONG).show();
                        break;
                    case "SEEK_TO_POSITION":
                        Toast.makeText(getApplicationContext(), "Seek to >> " + seek_pos, Toast.LENGTH_LONG).show();
                        break;
                    default:
                        Log.d(TAG, result);
                        Toast.makeText(getApplicationContext(), R.string.server_response_NULL, Toast.LENGTH_LONG).show();
                        network_status.setIcon(R.drawable.wlan_icon_red);
                        break;
                }
            } else {
                //track_info.setText(R.string.server_response_NULL);
                Toast.makeText(getApplicationContext(), R.string.server_response_NULL, Toast.LENGTH_LONG).show();
                network_status.setIcon(R.drawable.wlan_icon_red);
            }
        }
    }

    // Download and set Album Art
    public class ImageLoadTask extends AsyncTask<Void, Void, Bitmap> {

        private String url;
        private ImageView imageView;

        public ImageLoadTask(String url, ImageView imageView) {
            //Log.d(TAG, url);
            this.url = url;
            this.imageView = imageView;
        }

        @Override
        protected Bitmap doInBackground(Void... params) {
            try {
                if (url != null) {
                    URL urlConnection = new URL(url);
                    HttpURLConnection connection = (HttpURLConnection) urlConnection
                            .openConnection();
                    connection.setDoInput(true);
                    connection.connect();
                    InputStream input = connection.getInputStream();
                    Bitmap myBitmap = BitmapFactory.decodeStream(input);
                    return myBitmap;
                } else {
                    return null;
                }

            } catch (Exception e) {
                e.printStackTrace();
            }
            return null;
        }

        @Override
        protected void onPostExecute(Bitmap result) {
            super.onPostExecute(result);
            imageView.setImageBitmap(result);
        }
    }

    // Scheduled getServerStatus Custom Task
    public class ServerSyncTask extends TimerTask {
        private Handler handler;
        public ServerSyncTask(Handler h) {this.handler = h;}

        @Override
        public void run() {
            if (checkDisplayState()) {
                // Run getStatus here
                sendToServer = "get_state";
                //new getServerStatus().execute("");
                new SyncState().execute("");
            }

            // Update UI using the handler
            handler.post(new Runnable() {
                public void run() {
                    //update UI here
                }
            });
        }
    }
}