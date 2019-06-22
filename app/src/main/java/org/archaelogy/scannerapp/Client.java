package org.archaelogy.scannerapp;

import android.os.AsyncTask;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.PrintWriter;
import java.net.Socket;
import java.net.UnknownHostException;

public class Client extends AsyncTask<Void, String, String> {

    String dstAddress;
    int dstPort;
    String response = "";
    ScannerInfo activity;
    public Socket socket = null;

    PrintWriter out;

    Client(String addr, int port, ScannerInfo activity) {
        dstAddress = addr;
        dstPort = port;
        this.activity = activity;
    }

    @Override
    protected String doInBackground(Void... arg0) {

        try {
            socket = new Socket(dstAddress, dstPort);

            ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream(
                    1024);
            byte[] buffer = new byte[1024];

            InputStream inputStream = socket.getInputStream();
            OutputStream outstream = socket .getOutputStream();
            out = new PrintWriter(outstream);

			/*
             * notice: inputStream.read() will block if no data return
			 */
            while (inputStream.read(buffer) != -1) {
                response = new String(buffer, "utf8" ).trim(); //trim removes excess empty chars
                publishProgress(response);
                //Log.d("loop", response);
                buffer = new byte[1024];
            }

        } catch (UnknownHostException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
            response = "UnknownHostException: " + e.toString();
            activity.onFailedConnect(response);
        } catch (IOException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
            response = "IOException: " + e.toString();
            activity.onFailedConnect(response);
        } finally {
            if (socket != null) {
                try {
                    socket.close();
                    activity.sendGoodResult(response);
                } catch (IOException e) {
                    // TODO Auto-generated catch block
                    e.printStackTrace();
                }
            }
        }
        return response;
    }

    @Override
    protected void onProgressUpdate(String... values){
        //Log.d("client", values[0]);
        activity.toastForResponse(values[0]);
    }

    @Override
    protected void onPostExecute(String result) {
        //textResponse.setText(response);
        super.onPostExecute(result);
    }

    public void sendMessage(String message){
        out.print(message);
        out.flush();
    }

}
