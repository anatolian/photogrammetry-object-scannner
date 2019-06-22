package org.archaelogy.scannerapp;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Bundle;
import android.os.StrictMode;
import android.text.TextUtils;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ProgressBar;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.TextView;
import android.widget.Toast;

import org.w3c.dom.Text;

public class ScannerInfo extends Activity {

    boolean scanning = false;
    Button buttonScanStart;

    ProgressBar progressBar;
    TextView progressBarText;

    public void enableStrictMode()
    {
        StrictMode.ThreadPolicy policy = new StrictMode.ThreadPolicy.Builder().permitAll().build();

        StrictMode.setThreadPolicy(policy);
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_scanner_info);

        final EditText textBaseDir = findViewById(R.id.directoryEditText);
        final RadioGroup radioGroup = findViewById(R.id.HemisphereRadio);
        final EditText textLong = findViewById(R.id.LongitudeEditText);
        final EditText textEast = findViewById(R.id.EastingEditText);
        final EditText textNorth = findViewById(R.id.NorthingEditText);
        final EditText textId = findViewById(R.id.IdentifierEditText);
        final RadioButton RadioButtonN = findViewById(R.id.HemisphereRadioN);
        final RadioButton RadioButtonS = findViewById(R.id.HemisphereRadioS);

        progressBar = findViewById(R.id.determinateBar);
        progressBarText = findViewById(R.id.progressBarText);

        Intent intent = getIntent();

        String addr = intent.getStringExtra("addr");
        int port = intent.getIntExtra("port", 0);

        enableStrictMode();
        final Client myClient = new Client(addr, port, this);
        myClient.execute();

        buttonScanStart = (Button) findViewById(R.id.buttonScanStart);

        SharedPreferences settings = getApplicationContext().getSharedPreferences("ScannerAppSettings", 0);
        String baseDir = settings.getString("baseDir", "");
        String hemisphere = settings.getString("hemisphere", "N");
        String longitude = settings.getString("longitude", "");
        String easting = settings.getString("easting", "");
        String northing = settings.getString("northing", "");
        String identifier = settings.getString("identifier", "");

        textBaseDir.setText(baseDir);
        if(hemisphere.equals("N")){
            RadioButtonN.setChecked(true);
        } else RadioButtonS.setChecked(true);
        textLong.setText(longitude);
        textEast.setText(easting);
        textNorth.setText(northing);
        textId.setText(identifier);

        buttonScanStart.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {

                if(!scanning){

                    String baseDir = textBaseDir.getText().toString();
                    String hemisphere = "";
                    int checkedId = radioGroup.getCheckedRadioButtonId();
                    if(checkedId == R.id.HemisphereRadioN){
                        hemisphere = "N";
                    }else if(checkedId == R.id.HemisphereRadioS){
                        hemisphere = "S";
                    } else ;
                    String longitude = textLong.getText().toString();
                    String easting = textEast.getText().toString();
                    String northing = textNorth.getText().toString();
                    String identifier = textId.getText().toString();

                    if(TextUtils.isEmpty(baseDir) || TextUtils.isEmpty(hemisphere) || TextUtils.isEmpty(longitude) || TextUtils.isEmpty(easting) || TextUtils.isEmpty(northing) || TextUtils.isEmpty(identifier)){
                        Toast.makeText(getApplicationContext(), "Please fill in all fields", Toast.LENGTH_SHORT).show();
                        return;
                    }

                    String message = baseDir + "/" + hemisphere + "/" + longitude + "/" + easting + "/" + northing + "/" + identifier;
                    myClient.sendMessage(message);

                    //save inputs just entered, to make entering info less repetitive
                    SharedPreferences settings = getApplicationContext().getSharedPreferences("ScannerAppSettings", 0);
                    SharedPreferences.Editor editor = settings.edit();
                    editor.putString("baseDir", baseDir);
                    editor.putString("hemisphere", hemisphere);
                    editor.putString("longitude", longitude);
                    editor.putString("easting", easting);
                    editor.putString("northing", northing);
                    editor.putString("identifier", identifier);
                    editor.commit();

                    buttonScanStart.setText("Cancel Scan");
                } else {
                    myClient.sendMessage("cancel");
                    buttonScanStart.setText("Begin Scan");
                }
                scanning = !scanning;

            }
        });
    }

    public void toastForResponse(String message){
        //Log.d("main", message);
        if(message.equals("Connected!")){
            buttonScanStart.setText("Begin Scan");
            buttonScanStart.setEnabled(true);
            Toast.makeText(getApplicationContext(), message, Toast.LENGTH_SHORT).show();
        }
        else if(message.equals("done")){
            buttonScanStart.setText("Begin Scan");
            scanning = false;
            progressBar.setVisibility(View.GONE);
            progressBarText.setText("");
            Toast.makeText(getApplicationContext(), message, Toast.LENGTH_SHORT).show();
        }
        //progress update
        else{
            try{
                String percentage = message.substring(0,3);
                String descriptionText = message.substring(3);
                progressBar.setVisibility(View.VISIBLE);
                progressBar.setProgress(Integer.parseInt(percentage));
                String progressText = Integer.toString(Integer.parseInt(percentage)) + descriptionText;
                progressBarText.setText(progressText);
            } catch(Exception e) {
                // just skip progress update if somehow something's wrong
                progressBarText.setText(message);
            }
        }
    }

    public void onFailedConnect(String response){
        Intent data = new Intent();
//---set the data to pass back---
        data.setData(Uri.parse(response));
        setResult(RESULT_CANCELED, data);
//---close the activity---
        finish();
    }

    public void sendGoodResult(String response){
        Intent data = new Intent();
//---set the data to pass back---
        data.setData(Uri.parse(response));
        setResult(RESULT_OK, data);
//---close the activity---
        finish();
    }
}
