package org.archaelogy.scannerapp;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.RadioButton;
import android.widget.RadioGroup;
import android.widget.Toast;

import org.w3c.dom.Text;

public class ScannerInfo extends Activity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_scanner_info);

        Intent intent = getIntent();

        String addr = intent.getStringExtra("addr");
        int port = intent.getIntExtra("port", 0);

        final Client myClient = new Client(addr, port, this);
        myClient.execute();

        Button buttonScanStart = (Button) findViewById(R.id.buttonScanStart);

        final String[] hemisphere = {"N"};

        buttonScanStart.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                //TODO: convert text box input to directory name

                EditText textBaseDir = findViewById(R.id.directoryEditText);
                RadioGroup radioGroup = findViewById(R.id.HemisphereRadio);
                EditText textLong = findViewById(R.id.LongitudeEditText);
                EditText textEast = findViewById(R.id.EastingEditText);
                EditText textNorth = findViewById(R.id.NorthingEditText);
                EditText textId = findViewById(R.id.IdentifierEditText);

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
                //TODO:
                SharedPreferences settings = getApplicationContext().getSharedPreferences("ScannerAppSettings", 0);
                SharedPreferences.Editor editor = settings.edit();
                editor.putString("hemisphere", "");
            }
        });
    }

    public void toastForResponse(String message){
        //Log.d("main", message);
        Toast.makeText(getApplicationContext(), message, Toast.LENGTH_SHORT).show();
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
