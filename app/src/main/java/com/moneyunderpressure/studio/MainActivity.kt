package com.moneyunderpressure.studio

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

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
    var title by remember { mutableStateOf("") }
    var topic by remember { mutableStateOf("") }
    var selected by remember { mutableStateOf("Dashboard") }
    var notice by remember { mutableStateOf("Your production workspace is ready.") }

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
                                Text("CREATE A VIDEO", fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                            }
                            Text("VIDEO TITLE", color = Muted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                            StudioField(title, { title = it }, "e.g. Why Everyone Is in Debt")
                            Text("VIDEO IDEA / TOPIC", color = Muted, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                            StudioField(topic, { topic = it }, "Describe the story you want to tell")
                            Button(
                                onClick = {
                                    notice = if (title.isBlank() || topic.isBlank()) {
                                        "Add a title and topic to create your project."
                                    } else {
                                        "Draft project created: $title"
                                    }
                                },
                                modifier = Modifier.fillMaxWidth().height(52.dp),
                                colors = ButtonDefaults.buttonColors(containerColor = Cyan, contentColor = Ink),
                                shape = RoundedCornerShape(14.dp)
                            ) {
                                Icon(Icons.Default.AutoAwesome, null)
                                Spacer(Modifier.width(8.dp))
                                Text("CREATE PROJECT", fontWeight = FontWeight.Bold)
                            }
                            Text(notice, color = if (notice.startsWith("Draft")) Cyan else Muted, fontSize = 12.sp)
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
                    Card(
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF151D38)),
                        shape = RoundedCornerShape(18.dp)
                    ) {
                        Row(Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                            Icon(Icons.Default.PlayArrow, null, tint = Violet, modifier = Modifier.size(30.dp))
                            Spacer(Modifier.width(12.dp))
                            Column {
                                Text("THE STUDIO VISION", fontWeight = FontWeight.Bold)
                                Text("Cinematic 2D graphics • animated charts • kinetic typography",
                                    color = Muted, fontSize = 12.sp)
                            }
                        }
                    }
                }
                item {
                    Text("BUILD STATUS", fontWeight = FontWeight.Bold, letterSpacing = 1.sp)
                    Text("Foundation UI • First development milestone", color = Muted, fontSize = 13.sp)
                    LinearProgressIndicator(
                        progress = { 0.15f },
                        modifier = Modifier.fillMaxWidth().height(6.dp),
                        color = Cyan,
                        trackColor = Panel
                    )
                    Text("15% — Dashboard foundation", color = Cyan, fontSize = 12.sp)
                }
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
