package com.moneyunderpressure.studio

import android.content.ContentValues
import android.content.Context
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

object RenderApi {
    suspend fun renderProject(context: Context, project: StudioProject, onStatus: (String) -> Unit): String {
        val baseUrl = StudioSettings.baseUrl(context).trimEnd('/')
        val token = StudioSettings.token(context)
        require(baseUrl.startsWith("https://")) { "Enter a secure HTTPS render-server URL in Settings." }
        require(!token.isNullOrBlank()) { "Add your render API token in Settings." }
        onStatus("Sending project to renderer…")
        val jobId = withContext(Dispatchers.IO) { createJob(baseUrl, token, project) }
        onStatus("Render queued…")
        repeat(1800) {
            delay(2000)
            val status = withContext(Dispatchers.IO) { getStatus(baseUrl, token, jobId) }
            onStatus("Renderer: $status")
            when (status) {
                "completed" -> {
                    onStatus("Downloading finished MP4…")
                    return withContext(Dispatchers.IO) { download(context, baseUrl, token, jobId, project.title) }
                }
                "failed" -> throw IllegalStateException("The render server reported a failed job.")
            }
        }
        throw IllegalStateException("Render is taking longer than expected. Check the project again later.")
    }

    private fun connection(url: String, token: String) =
        (URL(url).openConnection() as HttpURLConnection).apply {
            connectTimeout = 20000
            readTimeout = 1800000
            setRequestProperty("Authorization", "Bearer $token")
        }

    private fun createJob(base: String, token: String, project: StudioProject): String {
        val body = JSONObject()
            .put("title", project.title)
            .put("subtitle", project.topic)
            .put("channel", "MONEY UNDER PRESSURE")
            .put("duration_seconds", 12)
            .put("fps", 30)
            .put("chart", org.json.JSONArray())
            .put("script", project.script.ifBlank { project.topic })
        val conn = connection("$base/v1/renders", token)
        conn.requestMethod = "POST"
        conn.doOutput = true
        conn.setRequestProperty("Content-Type", "application/json")
        conn.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
        val code = conn.responseCode
        val stream = if (code in 200..299) conn.inputStream else conn.errorStream
        val response = stream.bufferedReader().use { it.readText() }
        conn.disconnect()
        if (code !in 200..299) throw IllegalStateException("Render request failed ($code): $response")
        return JSONObject(response).getString("job_id")
    }

    private fun getStatus(base: String, token: String, jobId: String): String {
        val conn = connection("$base/v1/renders/$jobId", token)
        val code = conn.responseCode
        val stream = if (code in 200..299) conn.inputStream else conn.errorStream
        val response = stream.bufferedReader().use { it.readText() }
        conn.disconnect()
        if (code !in 200..299) throw IllegalStateException("Status check failed ($code): $response")
        return JSONObject(response).optString("status", "unknown")
    }

    private fun download(context: Context, base: String, token: String, jobId: String, title: String): String {
        val conn = connection("$base/v1/renders/$jobId/download", token)
        val code = conn.responseCode
        if (code !in 200..299) {
            val error = conn.errorStream?.bufferedReader()?.use { it.readText() } ?: "Download failed"
            conn.disconnect()
            throw IllegalStateException("MP4 download failed ($code): $error")
        }
        val safeName = title.replace(Regex("[^A-Za-z0-9_-]"), "_").take(48)
        val stamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.US).format(Date())
        val fileName = "MUP_" + safeName + "_" + stamp + ".mp4"
        val resolver = context.contentResolver
        val values = ContentValues().apply {
            put(MediaStore.Video.Media.DISPLAY_NAME, fileName)
            put(MediaStore.Video.Media.MIME_TYPE, "video/mp4")
            if (Build.VERSION.SDK_INT >= 29) {
                put(MediaStore.Video.Media.RELATIVE_PATH, Environment.DIRECTORY_MOVIES + "/Money Under Pressure")
                put(MediaStore.Video.Media.IS_PENDING, 1)
            }
        }
        val uri = resolver.insert(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, values)
        if (uri != null) {
            try {
                resolver.openOutputStream(uri)?.use { output ->
                    conn.inputStream.use { input -> input.copyTo(output) }
                } ?: throw IllegalStateException("Could not open the video output file.")
                if (Build.VERSION.SDK_INT >= 29) {
                    val ready = ContentValues().apply { put(MediaStore.Video.Media.IS_PENDING, 0) }
                    resolver.update(uri, ready, null, null)
                }
            } catch (e: Exception) {
                resolver.delete(uri, null, null)
                throw e
            } finally {
                conn.disconnect()
            }
            return "Saved to Movies/Money Under Pressure/" + fileName
        }
        val folder = context.getExternalFilesDir(Environment.DIRECTORY_MOVIES)
            ?: throw IllegalStateException("Phone storage is unavailable.")
        val file = File(folder, fileName)
        try {
            file.outputStream().use { output ->
                conn.inputStream.use { input -> input.copyTo(output) }
            }
        } finally {
            conn.disconnect()
        }
        return "Saved to app Movies folder: " + file.name
    }
}
