package com.moneyunderpressure.studio

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

object ProjectStore {
    private const val PREFS = "money_under_pressure_studio"
    private const val KEY_PROJECTS = "projects"

    fun load(context: Context): List<StudioProject> {
        val raw = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .getString(KEY_PROJECTS, "[]") ?: "[]"
        return try {
            val array = JSONArray(raw)
            buildList {
                for (i in 0 until array.length()) {
                    val item = array.getJSONObject(i)
                    add(
                        StudioProject(
                            id = item.optLong("id"),
                            title = item.optString("title"),
                            topic = item.optString("topic"),
                            createdAt = item.optLong("createdAt"),
                            script = item.optString("script")
                        )
                    )
                }
            }.sortedByDescending { it.createdAt }
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun save(context: Context, projects: List<StudioProject>) {
        val array = JSONArray()
        projects.forEach { project ->
            array.put(
                JSONObject()
                    .put("id", project.id)
                    .put("title", project.title)
                    .put("topic", project.topic)
                    .put("createdAt", project.createdAt)
                    .put("script", project.script)
            )
        }
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
            .edit()
            .putString(KEY_PROJECTS, array.toString())
            .apply()
    }
}
