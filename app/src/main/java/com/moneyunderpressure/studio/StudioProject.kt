package com.moneyunderpressure.studio

data class StudioProject(
    val id: Long,
    val title: String,
    val topic: String,
    val createdAt: Long,
    val script: String = ""
)
