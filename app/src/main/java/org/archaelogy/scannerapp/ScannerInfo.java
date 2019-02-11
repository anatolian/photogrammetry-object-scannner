package org.archaelogy.scannerapp;

import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.support.v7.app.AppCompatActivity;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.Toast;

public class ScannerInfo extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_scanner_info);

        Client myClient;

        Intent intent = getIntent();

        String addr = intent.getStringExtra("addr");
        int port = intent.getIntExtra("port", 0);

        myClient = new Client(addr, port, this);
        myClient.execute();

        Button buttonScanStart = (Button) findViewById(R.id.buttonScanStart);

        buttonScanStart.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View view) {
                //TODO: convert text box input to directory name
                String message = "";
                Client.sendMessage(message);

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
