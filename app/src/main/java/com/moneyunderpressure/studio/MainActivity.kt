package com.moneyunderpressure.studio

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Movie
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.filled.VideoLibrary
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlinx.coroutines.launch

private val Ink = Color(0xFF080D1A)
private val Panel = Color(0xFF111B30)
private val Cyan = Color(0xFF35D7F2)
private val Violet = Color(0xFF9875FF)
private val Muted = Color(0xFF9AAAC4)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { StudioApp() }
    }
}

@Composable
fun StudioApp() {
    val context = LocalContext.current
    var title by remember { mutableStateOf("") }
    var topic by remember { mutableStateOf("") }
    var script by remember { mutableStateOf("") }
    var selected by remember { mutableStateOf("Dashboard") }
    var notice by remember { mutableStateOf("Projects are saved on this phone.") }
    var serverUrl by remember { mutableStateOf(StudioSettings.baseUrl(context)) }
    var tokenInput by remember { mutableStateOf("") }
    var renderNotice by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()
    val projects = remember {
        mutableStateListOf<StudioProject>().apply {
            addAll(ProjectStore.load(context))
        }
    }

    MaterialTheme(colorScheme = darkColorScheme(
        background = Ink, surface = Panel, primary = Cyan,
        secondary = Violet, onBackground = Color.White, onSurface = Color.White
    )) {
        Scaffold(containerColor = Ink, bottomBar = {
            NavigationBar(containerColor = Panel, contentColor = Cyan) {
                listOf("Dashboard", "Projects", "Settings").forEach { item ->
                    NavigationBarItem(
                        selected = selected == item,
                        onClick = { selected = item },
                        icon = {
                            Icon(
                                when (item) {
                                    "Projects" -> Icons.Default.VideoLibrary
                                    "Settings" -> Icons.Default.Settings
                                    else -> Icons.Default.AutoAwesome
                                }, contentDescription = item
                            )
                        },
                        label = { Text(item) },
                        colors = NavigationBarItemDefaults.colors(
                            selectedIconColor = Cyan, selectedTextColor = Cyan,
                            indicatorColor = Color(0xFF20334A),
                            unselectedIconColor = Muted, unselectedTextColor = Muted
                        )
                    )
                }
            }
        }) { padding ->
            LazyColumn(
                modifier = Modifier.fillMaxSize().background(Ink).padding(padding),
                contentPadding = PaddingValues(20.dp),
                verticalArrangement = Arrangement.spacedBy(18.dp)
            ) {
                item {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            Modifier.size(42.dp).background(
                                Brush.linearGradient(listOf(Cyan, Violet)),
                                RoundedCornerShape(13.dp)
                            ), contentAlignment = Alignment.Center
                        ) { Icon(Icons.Default.Movie, null, tint = Ink) }
                        Spacer(Modifier.width(12.dp))
                        Column {
                            Text("MONEY UNDER PRESSURE", fontSize = 14.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                            Text("STUDIO  •  CREATIVE COMMAND", color = Muted, fontSize = 10.sp, letterSpacing = 1.4.sp)
                        }
                    }
                }
                if (selected == "Dashboard") {
                    item {
                        Column {
                            Text("Make your next", color = Muted, fontSize = 15.sp)
                            Text("big money story.", fontSize = 30.sp, fontWeight = FontWeight.ExtraBold)
                            Text("From an idea to a cinematic video.", color = Muted, fontSize = 14.sp)
                        }
                    }
                    item {
                        Card(
                            shape = RoundedCornerShape(22.dp),
                            colors = CardDefaults.cardColors(containerColor = Panel),
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(Icons.Default.Add, null, tint = Cyan)
                                    Spacer(Modifier.width(8.dp))
                                    Text("CREATE A VIDEO PROJECT", fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                                }
                                Text("VIDEO TITLE", color = Muted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                StudioField(title, { title = it }, "e.g. Why Everyone Is in Debt")
                                Text("VIDEO IDEA / TOPIC", color = Muted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                StudioField(topic, { topic = it }, "Describe the story you want to tell")
                                Text("VIDEO SCRIPT (OPTIONAL)", color = Muted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                                OutlinedTextField(
                                    value = script,
                                    onValueChange = { script = it },
                                    modifier = Modifier.fillMaxWidth().heightIn(min = 120.dp),
                                    placeholder = { Text("Paste your narration script. The renderer will split it into visual scenes.") },
                                    minLines = 4,
                                    maxLines = 8
                                )
                                Button(
                                    onClick = {
                                        if (title.isBlank() || topic.isBlank()) {
                                            notice = "Enter both a title and a topic first."
                                        } else {
                                            val project = StudioProject(
                                                id = System.currentTimeMillis(),
                                                title = title.trim(),
                                                topic = topic.trim(),
                                                createdAt = System.currentTimeMillis(),
                                                script = script.trim()
                                            )
                                            projects.add(0, project)
                                            ProjectStore.save(context, projects)
                                            notice = "Project saved on this phone."
                                            title = ""
                                            topic = ""
                                            script = ""
                                            selected = "Projects"
                                        }
                                    },
                                    modifier = Modifier.fillMaxWidth().height(52.dp),
                                    colors = ButtonDefaults.buttonColors(containerColor = Cyan, contentColor = Ink),
                                    shape = RoundedCornerShape(14.dp)
                                ) {
                                    Icon(Icons.Default.AutoAwesome, null)
                                    Spacer(Modifier.width(8.dp))
                                    Text("SAVE VIDEO PROJECT", fontWeight = FontWeight.Bold)
                                }
                                Text(notice, color = Cyan, fontSize = 12.sp)
                            }
                        }
                    }
                    item {
                        Text("PRODUCTION PIPELINE", fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                        Row(horizontalArrangement = Arrangement.spacedBy(9.dp)) {
                            PipelineTile("01", "Script", "Story & research", Modifier.weight(1f))
                            PipelineTile("02", "Visuals", "Motion design", Modifier.weight(1f))
                            PipelineTile("03", "Render", "MP4 export", Modifier.weight(1f))
                        }
                    }
                    item {
                        Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF151D38)),
                            shape = RoundedCornerShape(18.dp)) {
                            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(5.dp)) {
                                Text("VIDEO FORMAT", color = Cyan, fontWeight = FontWeight.Bold, fontSize = 11.sp)
                                Text("Long video: 16:9 landscape", fontWeight = FontWeight.SemiBold)
                                Text("Auto-create 4 vertical 9:16 Shorts from every narration script", fontWeight = FontWeight.SemiBold, color = Cyan)
                                Text("Visual identity: navy, cyan, violet, animated charts and kinetic type.",
                                    color = Muted, fontSize = 12.sp)
                            }
                        }
                    }
                } else if (selected == "Projects") {
                    item {
                        Text("YOUR PROJECTS", fontSize = 26.sp, fontWeight = FontWeight.ExtraBold)
                        Text("Saved locally on this device", color = Muted, fontSize = 13.sp)
                    }
                    if (projects.isEmpty()) {
                        item {
                            Card(colors = CardDefaults.cardColors(containerColor = Panel),
                                shape = RoundedCornerShape(18.dp)) {
                                Text("No projects yet. Create your first video from the Dashboard.",
                                    Modifier.padding(18.dp), color = Muted)
                            }
                        }
                    } else {
                        items(projects, key = { it.id }) { project ->
                            ProjectCard(project) {
                                scope.launch {
                                    renderNotice = "Preparing " + project.title
                                    try {
                                        renderNotice = RenderApi.renderProject(context, project) { status ->
                                            renderNotice = status
                                        }
                                    } catch (error: Exception) {
                                        renderNotice = error.message ?: "Render failed."
                                    }
                                }
                            }
                        }
                        if (renderNotice.isNotBlank()) {
                            item {
                                Card(colors = CardDefaults.cardColors(containerColor = Color(0xFF151D38)),
                                    shape = RoundedCornerShape(16.dp)) {
                                    Text(renderNotice, Modifier.padding(16.dp), color = Cyan, fontSize = 13.sp)
                                }
                            }
                        }
                    }
                } else {
                    item {
                        Text("STUDIO SETTINGS", fontSize = 26.sp, fontWeight = FontWeight.ExtraBold)
                        Card(colors = CardDefaults.cardColors(containerColor = Panel),
                            shape = RoundedCornerShape(18.dp)) {
                            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                                Text("RENDER SERVER CONNECTION", fontWeight = FontWeight.Bold, color = Cyan)
                                Text("Paste your private HTTPS render-server address here after the server is deployed.",
                                    color = Muted, fontSize = 12.sp)
                                StudioField(serverUrl, { serverUrl = it }, "https://your-render-server.onrender.com")
                                OutlinedTextField(
                                    value = tokenInput,
                                    onValueChange = { tokenInput = it },
                                    modifier = Modifier.fillMaxWidth(),
                                    label = { Text("Render API token") },
                                    placeholder = { Text("Leave blank to keep saved token") },
                                    singleLine = true,
                                    visualTransformation = PasswordVisualTransformation()
                                )
                                Button(
                                    onClick = {
                                        StudioSettings.saveBaseUrl(context, serverUrl)
                                        val tokenSaved = tokenInput.isBlank() || StudioSettings.saveToken(context, tokenInput)
                                        tokenInput = ""
                                        notice = if (tokenSaved) "Connection settings saved securely on this phone."
                                            else "Could not secure the API token on this device."
                                    },
                                    modifier = Modifier.fillMaxWidth(),
                                    colors = ButtonDefaults.buttonColors(containerColor = Cyan, contentColor = Ink)
                                ) { Text("SAVE CONNECTION", fontWeight = FontWeight.Bold) }
                                Text(if (StudioSettings.hasToken(context)) "API token: saved encrypted on this phone"
                                    else "API token: not configured", color = Muted, fontSize = 11.sp)
                                Text(notice, color = Cyan, fontSize = 12.sp)
                            }
                        }
                        Card(colors = CardDefaults.cardColors(containerColor = Panel),
                            shape = RoundedCornerShape(18.dp)) {
                            Column(Modifier.padding(18.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                Text("PRODUCTION PROFILE", fontWeight = FontWeight.Bold)
                                Text("Channel: Money Under Pressure", color = Muted)
                                Text("Look: cinematic premium motion graphics", color = Muted)
                                Text("Palette: dark navy • cyan • purple", color = Muted)
                                Text("Canvas: 16:9 landscape", color = Muted)
                            }
                        }
                        Text("Once the render server is deployed and connected, use Render MP4 on a saved project.",
                            color = Cyan, fontSize = 13.sp)
                    }
                }
            }
        }
    }
}

@Composable
private fun ProjectCard(project: StudioProject, onRender: () -> Unit) {
    val date = remember(project.createdAt) {
        SimpleDateFormat("dd MMM yyyy, HH:mm", Locale.getDefault()).format(Date(project.createdAt))
    }
    Card(colors = CardDefaults.cardColors(containerColor = Panel),
        shape = RoundedCornerShape(17.dp), modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Movie, null, tint = Cyan)
                Spacer(Modifier.width(9.dp))
                Text(project.title, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            }
            Text(project.topic, color = Muted, fontSize = 13.sp)
            Text("CREATED $date  •  DRAFT", color = Violet, fontSize = 10.sp, fontWeight = FontWeight.Bold)
            Button(
                onClick = onRender,
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = Cyan, contentColor = Ink)
            ) {
                Icon(Icons.Default.PlayArrow, null)
                Spacer(Modifier.width(8.dp))
                Text("RENDER MP4", fontWeight = FontWeight.Bold)
            }
        }
    }
}

@Composable
private fun StudioField(value: String, onValueChange: (String) -> Unit, hint: String) {
    BasicTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = Modifier.fillMaxWidth().background(Color(0xFF0A1222), RoundedCornerShape(12.dp)).padding(14.dp),
        textStyle = androidx.compose.ui.text.TextStyle(color = Color.White, fontSize = 14.sp),
        decorationBox = { inner ->
            Box {
                if (value.isEmpty()) Text(hint, color = Muted, fontSize = 14.sp)
                inner()
            }
        }
    )
}

@Composable
private fun PipelineTile(number: String, name: String, detail: String, modifier: Modifier = Modifier) {
    Column(
        modifier.background(Panel, RoundedCornerShape(15.dp)).padding(12.dp),
        verticalArrangement = Arrangement.spacedBy(5.dp)
    ) {
        Text(number, color = Cyan, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        Text(name, fontWeight = FontWeight.Bold, fontSize = 14.sp)
        Text(detail, color = Muted, fontSize = 10.sp, lineHeight = 13.sp)
    }
}
